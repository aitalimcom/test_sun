import logging
import os
import pandas as pd
from typing import Any
from pathlib import Path
from core.agent import BaseAgent
from core.state import AgentState
from config import settings
from prompts.templates.table_query import TABLE_QUERY_SYSTEM_PROMPT, TABLE_QUERY_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class TableAgent(BaseAgent):
    """Loads agricultural telemetry/price/weather CSV datasets and responds to mathematical/tabular queries."""

    name = "table_query"
    description = "डाटा तालिका विश्लेषक - मौसम इतिहास, आईओटी रिडिङ वा बजार भाउ डाटासेटको गणितीय विश्लेषण"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return TABLE_QUERY_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Table query agent...")
        dispatch_query = state.get("dispatch_query", "")

        # Locate CSV databases
        csv_dir = Path(settings.database_root) / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        
        weather_csv = csv_dir / "weather_history.csv"
        price_csv = csv_dir / "price_history.csv"
        iot_csv = csv_dir / "iot_telemetry.csv"

        # Check if they exist, otherwise seed mock columns for prompt context
        cols_summary = {}
        samples = {}
        dataframes = {}

        if weather_csv.exists():
            try:
                df = pd.read_csv(weather_csv)
                cols_summary["weather_history"] = list(df.columns)
                samples["weather_history"] = df.head(2).to_dict(orient="records")
                dataframes["weather"] = df
            except Exception as e:
                logger.warning(f"Error reading weather CSV: {e}")
                
        if price_csv.exists():
            try:
                df = pd.read_csv(price_csv)
                cols_summary["price_history"] = list(df.columns)
                samples["price_history"] = df.head(2).to_dict(orient="records")
                dataframes["price"] = df
            except Exception as e:
                logger.warning(f"Error reading price CSV: {e}")

        if iot_csv.exists():
            try:
                df = pd.read_csv(iot_csv)
                cols_summary["iot_telemetry"] = list(df.columns)
                samples["iot_telemetry"] = df.head(2).to_dict(orient="records")
                dataframes["iot"] = df
            except Exception as e:
                logger.warning(f"Error reading IoT CSV: {e}")

        # Fallback to direct prompt reasoning if dataframes list is empty
        if not dataframes:
            logger.warning("No CSV files found in database/csv. Falling back to text-based mock tables.")
            cols_summary = {
                "weather_history": ["date", "temp", "humidity", "rainfall"],
                "price_history": ["date", "crop", "market", "min_price", "max_price"],
                "iot_telemetry": ["timestamp", "device_id", "soil_moisture", "npk_nitrogen"]
            }
            samples = {
                "weather_history": [{"date": "2026-07-30", "temp": 28, "humidity": 80, "rainfall": 12}],
                "price_history": [{"date": "2026-07-30", "crop": "potato", "market": "kalimati", "min_price": 60, "max_price": 70}]
            }

        # Let's try to run LangChain experimental pandas agent if requested and possible
        # Since running generated code is dangerous, we secure it or use a default structured query logic.
        try:
            from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
            
            # Use list of loaded dataframes if available
            dfs = list(dataframes.values())
            if dfs:
                # Initialize the pandas query agent
                # Note: allow_dangerous_code=True is required by langchain to execute Pandas queries locally.
                agent = create_pandas_dataframe_agent(
                    self.llm,
                    dfs[0] if len(dfs) == 1 else dfs,
                    verbose=False,
                    allow_dangerous_code=True,
                    max_iterations=3,
                )
                logger.info("Invoking pandas agent on CSV DataFrames...")
                response = await agent.ainvoke({"input": dispatch_query})
                output = response.get("output", "")
                
                # Check if output is standard text, we can translate it if it's in English
                translated_output = await self._translate_result(output)
                return {
                    "result": translated_output,
                    "success": True,
                    "new_messages": [{"role": "assistant", "content": translated_output}],
                }
        except Exception as e:
            logger.warning(f"LangChain pandas agent execution skipped or failed: {e}. Falling back to prompt advisory.")

        # Final prompt fallback
        user_prompt = TABLE_QUERY_USER_PROMPT.format(
            query=dispatch_query,
            columns=str(cols_summary),
            samples=str(samples)
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            return {
                "result": content,
                "success": True,
                "new_messages": [{"role": "assistant", "content": content}],
            }
        except Exception as e:
            logger.error(f"Table agent execution failed: {e}")
            return {
                "result": "डाटा तालिका विश्लेषण गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }

    async def _translate_result(self, text: str) -> str:
        """Helper to translate the pandas execution results to standard Nepali."""
        try:
            from core.multimodal.language_normalizer import LanguageNormalizer
            normalizer = LanguageNormalizer()
            return await normalizer.normalize(text)
        except Exception:
            return text
