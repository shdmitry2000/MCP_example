#!/usr/bin/env python3
# streamlit_gui_dbcreator.py

"""
Streamlit GUI for Schema Conversion and Data Generation
Provides a user-friendly interface for both processes
"""

import streamlit as st
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import logging

# Configure logging for Streamlit app
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler() # Ouputs to console, visible when running streamlit
    ]
)
logger = logging.getLogger(__name__)

# Import our modules
try:
    # Assuming schema_converter.py defines SchemaConverter
    from syntetic_data_create.schema_converter import SchemaConverter
    # Assuming data_generator.py defines DataGenerationEngine
    from syntetic_data_create.data_generator import DataGenerationEngine
    from config.config import config
    # Use DB_FOLDER from config as a default
    DEFAULT_DB_FOLDER = getattr(config, 'DB_FOLDER', 'database_files')
except ImportError as e:
    st.error(f"Import error: {e}. Please ensure all modules are correctly placed and PYTHONPATH is set.")
    logger.error(f"Import error in Streamlit: {e}", exc_info=True)
    # Fallback if config or other modules are missing
    DEFAULT_DB_FOLDER = 'database_files'
    # Provide dummy classes if imports fail, so Streamlit can at least render an error page
    if 'SchemaConverter' not in globals():
        class SchemaConverter:
            def __init__(self, *args, **kwargs): pass
            def convert_swagger_to_definition(self, *args, **kwargs): return {"tables": {}}
            def save_definition_file(self, *args, **kwargs): pass
    if 'DataGenerationEngine' not in globals():
        class DataGenerationEngine:
            def __init__(self, *args, **kwargs): pass
            def generate_database(self, *args, **kwargs): return {"error": "DataGenerationEngine not loaded"}
            def export_data(self, *args, **kwargs): return {}
            def get_database_stats(self, *args, **kwargs): return {}
            def generate_report(self, *args, **kwargs): return {}
    st.stop()


# Page configuration
st.set_page_config(
    page_title="Israeli Banking Data Generator",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Hebrew support and styling
st.markdown("""
<style>
    .hebrew-text {
        direction: rtl;
        text-align: right;
        font-family: 'Arial', 'Helvetica', sans-serif;
    }
    .stSelectbox > div > div > div {
        font-family: 'Arial', 'Helvetica', sans-serif;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .process-container {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem; /* Increased padding */
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'conversion_result' not in st.session_state:
        st.session_state.conversion_result = None
    if 'generation_result' not in st.session_state:
        st.session_state.generation_result = None
    if 'db_folder' not in st.session_state:
        st.session_state.db_folder = str(Path(DEFAULT_DB_FOLDER).resolve())


def show_file_explorer(folder_path_str: str) -> List[str]:
    """Show file explorer for a folder."""
    folder = Path(folder_path_str)
    if not folder.exists():
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            st.error(f"Could not create folder {folder}: {e}")
            return []
        return []
    
    files = []
    try:
        for file_path in folder.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(folder)
                files.append(str(relative_path))
    except Exception as e:
        st.error(f"Error reading folder {folder}: {e}")
        return []
    
    return sorted(files)


def process_1_schema_conversion():
    """Process 1: Schema Conversion Interface."""
    st.markdown('<div class="process-container">', unsafe_allow_html=True)
    st.header("🔄 Process 1: Schema Conversion")
    st.write("Convert Swagger/OpenAPI files to a standardized Definition format.")
    
    input_method = st.radio(
        "Choose Swagger/OpenAPI input method:",
        ["Upload File", "Use Sample Israeli Banking Schema", "Paste JSON Content"],
        key="p1_input_method"
    )
    
    swagger_content_str = None
    swagger_filename = "swagger_schema.json"
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Upload Swagger/OpenAPI file (.json, .yaml, .yml)",
            type=["json", "yaml", "yml"],
            key="p1_swagger_upload"
        )
        if uploaded_file:
            try:
                swagger_content_str = uploaded_file.read().decode('utf-8')
                swagger_filename = uploaded_file.name
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")
                return
            
    elif input_method == "Use Sample Israeli Banking Schema":
        st.info("Using a built-in sample Israeli banking Swagger schema.")
        # A more comprehensive sample schema
        sample_schema = {
            "openapi": "3.0.0",
            "info": {"title": "Sample Israeli Banking API", "version": "1.0.1"},
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["תעודת_זהות", "שם_פרטי", "שם_משפחה"],
                        "properties": {
                            "תעודת_זהות": {"type": "string", "description": "מספר תעודת זהות ישראלית", "pattern": "^[0-9]{9}$"},
                            "שם_פרטי": {"type": "string", "description": "שם פרטי בעברית", "maxLength": 50},
                            "שם_משפחה": {"type": "string", "description": "שם משפחה בעברית", "maxLength": 50},
                            "טלפון": {"type": "string", "description": "מספר טלפון ישראלי"}
                        }
                    },
                    "Account": {
                        "type": "object",
                        "properties": {
                             "מספר_חשבון": {"type": "string", "description": "מספר חשבון"},
                             "יתרה": {"type": "number", "format": "float", "description": "יתרת חשבון"}
                        }
                    }
                }
            }
        }
        swagger_content_str = json.dumps(sample_schema, ensure_ascii=False, indent=2)
        swagger_filename = "israeli_banking_sample.json"
        
    elif input_method == "Paste JSON Content":
        swagger_content_str = st.text_area(
            "Paste Swagger/OpenAPI JSON content here:",
            height=250,
            key="p1_swagger_text"
        )
        if swagger_content_str:
            swagger_filename = "pasted_swagger.json"

    col1, col2 = st.columns(2)
    with col1:
        target_system = st.selectbox(
            "Target Generation System for Definition:",
            ["faker", "sdv", "mimesis", "custom"],
            index=0,
            key="p1_target_system",
            help="Optimizes the definition for this target data generator."
        )
    with col2:
        def_file_stem = Path(swagger_filename).stem
        output_name = st.text_input(
            "Output Definition File Name (without .json):",
            value=f"{def_file_stem}_{target_system}",
            key="p1_output_name"
        )

    if st.button("🔄 Convert Schema", key="p1_convert_btn", type="primary"):
        if not swagger_content_str:
            st.warning("Please provide Swagger/OpenAPI content.")
            return
        if not output_name.strip():
            st.warning("Please provide an output file name.")
            return

        try:
            with st.spinner("Converting schema..."):
                converter = SchemaConverter()
                # SchemaConverter expects a dictionary
                if Path(swagger_filename).suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    swagger_schema_dict = yaml.safe_load(swagger_content_str)
                else:
                    swagger_schema_dict = json.loads(swagger_content_str)

                definition_schema = converter.convert_swagger_to_definition(swagger_schema_dict, target_system)
                
                definitions_folder = Path(st.session_state.db_folder) / "definitions"
                definitions_folder.mkdir(parents=True, exist_ok=True)
                definition_path = definitions_folder / f"{output_name.strip()}_definition.json"
                
                saved_file_path = converter.save_definition_file(definition_schema, str(definition_path))
                
                st.session_state.conversion_result = {
                    "definition_path": saved_file_path,
                    "definition_schema": definition_schema,
                    "target_system": target_system,
                    "tables_count": len(definition_schema.get("tables", {})),
                    "timestamp": datetime.now().isoformat()
                }
            st.success(f"✅ Schema conversion completed successfully!")
            logger.info(f"Schema converted: {saved_file_path}")

        except Exception as e:
            st.error(f"❌ Conversion failed: {e}")
            logger.error(f"Schema conversion failed: {e}", exc_info=True)

    if st.session_state.conversion_result:
        st.markdown('<hr><div class="success-box">', unsafe_allow_html=True)
        st.subheader("📊 Conversion Results")
        res = st.session_state.conversion_result
        st.markdown(f"""
        - **Definition File:** `{res['definition_path']}`
        - **Tables Created:** {res['tables_count']}
        - **Target System Hint:** {res['target_system']}
        - **Timestamp:** {res['timestamp']}
        """)
        if Path(res['definition_path']).exists():
             st.metric("File Size", f"{Path(res['definition_path']).stat().st_size / 1024:.1f} KB")

        if st.checkbox("Show Definition JSON Preview", key="p1_show_def_json"):
            st.json(res['definition_schema'])
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)


def process_2_data_generation():
    """Process 2: Data Generation Interface."""
    st.markdown('<div class="process-container">', unsafe_allow_html=True)
    st.header("🚀 Process 2: Data Generation")
    st.write("Generate a database from a Definition file.")

    definitions_folder = Path(st.session_state.db_folder) / "definitions"
    if not definitions_folder.exists():
        definitions_folder.mkdir(parents=True, exist_ok=True)
        
    definition_files = sorted([f for f in definitions_folder.glob("*.json") if f.is_file()])
    file_options = [f.name for f in definition_files]
    
    selected_def_file_name = None

    if st.session_state.conversion_result and Path(st.session_state.conversion_result["definition_path"]).exists():
        converted_def_name = Path(st.session_state.conversion_result["definition_path"]).name
        if converted_def_name not in file_options:
            file_options.insert(0, f"{converted_def_name} (from recent conversion)")
        selected_def_file_name = st.selectbox(
            "Select Definition File:", file_options, key="p2_def_file_select",
            index=0 if converted_def_name in file_options or file_options[0].endswith("(from recent conversion)") else (0 if file_options else None)
        )
    elif file_options:
        selected_def_file_name = st.selectbox("Select Definition File:", file_options, key="p2_def_file_select_no_conv")
    else:
        st.warning("No Definition files found in the 'definitions' subfolder. Please complete Process 1 first or manually add a definition file.")
        
        # Option to upload definition file if none exist
        uploaded_def_file = st.file_uploader(
            "Or, upload a definition file (.json):", type=["json"], key="p2_def_upload"
        )
        if uploaded_def_file:
            try:
                def_content = uploaded_def_file.read().decode('utf-8')
                def_path = definitions_folder / uploaded_def_file.name
                with open(def_path, 'w', encoding='utf-8') as f:
                    f.write(def_content)
                st.success(f"✅ Definition file '{uploaded_def_file.name}' uploaded and saved. Please re-select from the dropdown.")
                logger.info(f"Definition file uploaded: {def_path}")
                st.rerun() # Rerun to update the file_options
            except Exception as e:
                st.error(f"Error saving uploaded definition file: {e}")
        st.markdown('</div>', unsafe_allow_html=True) # Close process-container
        return

    if not selected_def_file_name:
        st.markdown('</div>', unsafe_allow_html=True) # Close process-container
        return

    actual_def_file_path = ""
    if "(from recent conversion)" in selected_def_file_name:
        actual_def_file_path = st.session_state.conversion_result["definition_path"]
    else:
        actual_def_file_path = str(definitions_folder / selected_def_file_name)

    st.info(f"Selected definition: `{actual_def_file_path}`")

    col_params1, col_params2 = st.columns(2)
    with col_params1:
        num_records = st.number_input("Number of Records per Table:", min_value=1, max_value=100000, value=100, step=10, key="p2_num_records")
        strategy = st.selectbox("Generation Strategy:", ["faker"], key="p2_gen_strategy", help="Method for data generation. More strategies can be added.")
    with col_params2:
        db_name_stem = Path(selected_def_file_name.replace(" (from recent conversion)", "")).stem.replace("_definition","")
        db_file_name = st.text_input("Output Database File Name (e.g., data.db):", value=f"{db_name_stem}.db", key="p2_db_name")
        custom_db_url_input = st.text_input("Custom Database URL (Optional):", placeholder="E.g., sqlite:///path/to/your.db or postgresql://...", key="p2_custom_db_url")

    with st.expander("🔧 Advanced Options & Export"):
        export_formats = st.multiselect(
            "Export Data to Formats:", ["csv", "json", "excel", "sql"], default=["csv"], key="p2_export_formats"
        )
        
        workflow_option = st.radio(
            "Workflow Execution:", 
            ["Complete Workflow", "Step by Step"],
            index=0,
            key="p2_workflow_option",
            help="Complete workflow runs all steps at once. Step by step allows manual execution of each step."
        )
        
        if workflow_option == "Step by Step":
            st.info("Step-by-step execution will be shown after clicking 'Generate Database'")

    if st.button("🚀 Generate Database", key="p2_generate_btn", type="primary"):
        if not actual_def_file_path or not Path(actual_def_file_path).exists():
            st.error("Selected definition file is invalid or does not exist.")
            return
        if not db_file_name.strip() and not custom_db_url_input.strip():
            st.warning("Please provide an output database file name or a custom DB URL.")
            return

        final_db_url = None
        if custom_db_url_input.strip():
            final_db_url = custom_db_url_input.strip()
        else:
            # Ensure db_file_name is just a name, not a path, to place it in db_folder
            db_file_path = Path(st.session_state.db_folder) / Path(db_file_name.strip()).name
            final_db_url = f"sqlite:///{db_file_path}"

        # Initialize the data generation engine
        engine = DataGenerationEngine(db_folder=st.session_state.db_folder)
        
        if workflow_option == "Complete Workflow":
            try:
                with st.spinner(f"Generating database ({strategy}, {num_records} records)... This may take a moment."):
                    # Use the complete workflow method
                    gen_result = engine.generate_complete_database(
                        definition_file=actual_def_file_path,
                        num_records=num_records,
                        strategy=strategy,
                        db_url=final_db_url,
                        export_formats=export_formats
                    )
                    
                    st.session_state.generation_result = {
                        "result": gen_result,
                        "export_result": gen_result.get("export_results", {}),
                        "report": gen_result.get("report_file"),
                        "db_url_used": gen_result.get("database_url", final_db_url),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                if gen_result.get("status") == "success":
                    st.success("✅ Database generation and export completed successfully!")
                    logger.info(f"Database generation successful: {final_db_url}")
                else:
                    st.error(f"❌ Database generation failed: {gen_result.get('message')}")
                    logger.error(f"Database generation failed: {gen_result.get('message')}")
                    
            except Exception as e:
                st.error(f"❌ Data Generation Failed: {e}")
                logger.error(f"Data generation failed: {e}", exc_info=True)
        else:
            # Step by step workflow
            try:
                st.write("### Step-by-Step Execution")
                
                # Step 1: Load definition file
                with st.spinner("Step 1: Loading definition file..."):
                    definition = engine.load_definition_file(actual_def_file_path)
                    st.success("✅ Definition file loaded successfully!")
                    st.json({"tables": list(definition.get("tables", {}).keys())})
                
                # Step 2: Prepare database URL
                with st.spinner("Step 2: Preparing database URL..."):
                    db_url = engine.prepare_database_url(final_db_url)
                    st.success(f"✅ Database URL prepared: {db_url}")
                
                # Step 3: Create generator
                with st.spinner(f"Step 3: Creating {strategy} generator..."):
                    generator = engine.create_generator(strategy)
                    st.success(f"✅ Generator created with strategy: {strategy}")
                
                # Step 4: Convert definition to generator schema
                with st.spinner("Step 4: Converting definition to generator schema..."):
                    generator_schema = engine.convert_definition_to_generator_schema()
                    st.success("✅ Definition converted to generator schema")
                    st.json({"tables": list(generator_schema.keys())})
                
                # Step 5: Generate database
                with st.spinner(f"Step 5: Generating database with {num_records} records..."):
                    generation_result = engine.generate_database_data(generator_schema, num_records)
                    st.success(f"✅ Database generated: {generation_result.get('database_url')}")
                    st.write(f"Tables created: {generation_result.get('tables_created')}")
                    st.write(f"Records per table: {generation_result.get('records_generated')}")
                
                # Step 6: Export data
                if export_formats:
                    with st.spinner(f"Step 6: Exporting data to {', '.join(export_formats)}..."):
                        export_result = engine.export_data(export_formats)
                        st.success("✅ Data exported successfully")
                        for format_name, format_info in export_result.items():
                            if "error" not in format_info:
                                st.write(f"{format_name.upper()}: {format_info.get('file_count', 0)} files in {format_info.get('location')}")
                            else:
                                st.warning(f"{format_name.upper()}: Failed - {format_info.get('error')}")
                
                # Step 7: Generate report
                with st.spinner("Step 7: Generating report..."):
                    report_result = engine.generate_report()
                    st.success(f"✅ Report generated: {report_result.get('report_file')}")
                
                # Store results for display
                st.session_state.generation_result = {
                    "result": generation_result,
                    "export_result": export_result if export_formats else {},
                    "report": report_result.get("report_file"),
                    "db_url_used": generation_result.get("database_url", final_db_url),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                st.error(f"❌ Step-by-Step workflow failed: {e}")
                logger.error(f"Step-by-Step workflow failed: {e}", exc_info=True)

    if st.session_state.generation_result:
        st.markdown('<hr><div class="success-box">', unsafe_allow_html=True)
        st.subheader("🎉 Generation Outcome")
        gen_output = st.session_state.generation_result
        res_data = gen_output["result"]
        
        st.markdown(f"""
        - **Database Location:** `{gen_output.get('db_url_used', 'N/A')}`
        - **Total Records Approx:** {res_data.get('total_records', res_data.get('records_generated', 'N/A'))}
        - **Tables Created:** {len(res_data.get('tables_created', []))}
        - **Strategy Used:** {res_data.get('strategy_used', 'N/A')}
        - **Timestamp:** {gen_output.get('timestamp')}
        """)
        
        db_size_mb = "N/A"
        if gen_output.get('db_url_used') and gen_output['db_url_used'].startswith("sqlite:///"):
            db_file = Path(gen_output['db_url_used'].replace("sqlite:///", ""))
            if db_file.exists():
                db_size_mb = f"{db_file.stat().st_size / (1024 * 1024):.2f} MB"
        st.metric("Database Size", db_size_mb)

        if st.checkbox("Show Detailed Generation Result", key="p2_show_gen_json"):
            st.json(res_data)

        export_info = gen_output.get("export_result", {})
        if export_info:
            st.subheader("📤 Export Details")
            for fmt, info in export_info.items():
                if isinstance(info, dict) and "error" not in info:
                    files_count = info.get("file_count", 0)
                    if files_count == 0 and isinstance(info.get("files"), dict):
                        files_count = len(info.get("files", {}))
                    
                    st.write(f"**{fmt.upper()}**: {files_count} file(s) in `{info.get('location', 'N/A')}`")
                    
                    # Show file details for SQL exports
                    if fmt == "sql" and st.checkbox(f"Show {fmt.upper()} files", key=f"show_{fmt}_files"):
                        for table_name, file_path in info.get("files", {}).items():
                            file_size = Path(file_path).stat().st_size / 1024 if Path(file_path).exists() else 0
                            st.write(f"- {table_name}.sql ({file_size:.1f} KB)")
                else:
                    error_msg = info.get('error') if isinstance(info, dict) else str(info)
                    st.error(f"**{fmt.upper()} Export Failed:** {error_msg}")

        if st.checkbox("Show Database Statistics", key="p2_show_stats"):
            if gen_output.get('db_url_used'):
                try:
                    # DataGenerationEngine is instantiated with db_folder
                    engine_for_stats = DataGenerationEngine(db_folder=st.session_state.db_folder)
                    stats = engine_for_stats.get_database_stats(db_url=gen_output['db_url_used'])
                    if stats and "error" not in stats:
                        stats_df_data = [{"Table": name, "Records": info.get('record_count', 0), "Columns": len(info.get('columns',[]))} for name, info in stats.items()]
                        st.dataframe(pd.DataFrame(stats_df_data), use_container_width=True)
                    elif "error" in stats:
                        st.warning(f"Could not retrieve stats: {stats['error']}")
                    else:
                        st.info("No statistics available.")
                except Exception as e:
                    st.error(f"Error fetching database statistics: {e}")
                    logger.error(f"Error fetching stats: {e}", exc_info=True)
            else:
                st.warning("Database URL not available to fetch statistics.")
                
        # Show report file option
        if "report" in gen_output and gen_output["report"]:
            report_file = gen_output["report"]
            if Path(report_file).exists():
                st.subheader("📊 Generation Report")
                if st.checkbox("Show Report Content", key="p2_show_report"):
                    try:
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            st.json(report_data)
                    except Exception as e:
                        st.error(f"Error reading report file: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
def file_manager():
    """File Manager Interface."""
    st.markdown('<div class="process-container">', unsafe_allow_html=True)
    st.header("📁 File Manager & Output Viewer")
    st.write(f"Viewing files within the configured database folder: `{st.session_state.db_folder}`")

    main_db_folder = Path(st.session_state.db_folder)
    
    tabs = st.tabs(["📋 Definitions", "🗄️ Databases (.db)", "📤 Exports", "📜 Logs", "📄 Reports"])

    with tabs[0]: # Definitions
        st.subheader("📋 Definition Files")
        def_folder = main_db_folder / "definitions"
        def_files = show_file_explorer(str(def_folder))
        if def_files:
            for f_rel_path in def_files:
                f_abs_path = def_folder / f_rel_path
                f_size_kb = f"{f_abs_path.stat().st_size / 1024:.1f} KB"
                st.markdown(f"- `{f_rel_path}` ({f_size_kb})")
        else:
            st.info("No definition files found in 'definitions' subfolder.")

    with tabs[1]: # Databases
        st.subheader("🗄️ Database Files (.db)")
        db_files_list = sorted([f for f in main_db_folder.glob("*.db") if f.is_file()])
        if db_files_list:
            for f_abs_path in db_files_list:
                f_size_mb = f"{f_abs_path.stat().st_size / (1024*1024):.2f} MB"
                st.markdown(f"- `{f_abs_path.name}` ({f_size_mb})")
        else:
            st.info("No .db files found directly in the database folder.")
            
    with tabs[2]: # Exports
        st.subheader("📤 Export Files")
        exports_folder_path = main_db_folder / "exports"
        export_files_list = show_file_explorer(str(exports_folder_path))
        if export_files_list:
            # Limit display for brevity
            for f_rel_path in export_files_list[:15]: 
                 f_abs_path = exports_folder_path / f_rel_path
                 f_size_kb = f"{f_abs_path.stat().st_size / 1024:.1f} KB"
                 st.markdown(f"- `{f_rel_path}` ({f_size_kb})")
            if len(export_files_list) > 15:
                st.markdown(f"... and {len(export_files_list) - 15} more files.")
        else:
            st.info("No export files found in 'exports' subfolder.")

    with tabs[3]: # Logs
        st.subheader("📜 Log Files")
        logs_folder_path = main_db_folder / "logs"
        log_files_list = show_file_explorer(str(logs_folder_path))
        if log_files_list:
            for f_rel_path in log_files_list:
                f_abs_path = logs_folder_path / f_rel_path
                f_size_kb = f"{f_abs_path.stat().st_size / 1024:.1f} KB"
                st.markdown(f"- `{f_rel_path}` ({f_size_kb})")
        else:
            st.info("No log files found in 'logs' subfolder.")
            
    with tabs[4]: # Reports
        st.subheader("📄 Generation Reports")
        # Reports are saved in db_folder directly by DataGenerationEngine
        report_files_list = sorted([f for f in main_db_folder.glob("generation_report_*.json") if f.is_file()])
        if report_files_list:
            for f_abs_path in report_files_list:
                f_size_kb = f"{f_abs_path.stat().st_size / 1024:.1f} KB"
                st.markdown(f"- `{f_abs_path.name}` ({f_size_kb})")
                if st.checkbox(f"View {f_abs_path.name}", key=f"view_report_{f_abs_path.name}"):
                    try:
                        with open(f_abs_path, 'r', encoding='utf-8') as rf:
                            st.json(json.load(rf))
                    except Exception as e_report:
                        st.error(f"Could not read report {f_abs_path.name}: {e_report}")
        else:
            st.info("No generation reports found.")
            
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    st.markdown('<h1 class="main-header">🏦 Israeli Banking Data Workbench</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        current_folder = st.session_state.db_folder
        new_db_folder_input = st.text_input(
            "Working Database Folder:",
            value=current_folder,
            key="db_folder_input_main",
            help="All generated files (databases, definitions, exports, logs) will be stored relative to this folder."
        )
        
        resolved_new_folder = str(Path(new_db_folder_input).resolve())

        if resolved_new_folder != current_folder:
            st.session_state.db_folder = resolved_new_folder
            # Clear results if folder changes significantly to avoid confusion
            st.session_state.conversion_result = None
            st.session_state.generation_result = None
            logger.info(f"DB Folder changed to: {resolved_new_folder}")
            st.rerun()
        
        st.info(f"Current folder: `{st.session_state.db_folder}`")
        Path(st.session_state.db_folder).mkdir(parents=True, exist_ok=True) # Ensure it exists

        st.header("🧭 Navigation")
        page = st.radio(
            "Select Workbench Section:",
            ["Schema Conversion", "Data Generation", "File Manager"],
            key="main_navigation"
        )
        
        st.header("📊 Process Status")
        if st.session_state.conversion_result:
            st.success("✅ Schema Converted")
        else:
            st.info("⏳ Schema Conversion Pending")
        
        if st.session_state.generation_result:
            st.success("✅ Database Generated")
        else:
            st.info("⏳ Database Generation Pending")

    # Main content based on navigation
    if page == "Schema Conversion":
        process_1_schema_conversion()
    elif page == "Data Generation":
        process_2_data_generation()
    elif page == "File Manager":
        file_manager()
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
            🏦 Israeli Banking Data Workbench | 
            Streamlit Interface v1.1 | All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    # Check if essential modules are available before running main
    if 'SchemaConverter' not in globals() or 'DataGenerationEngine' not in globals() or 'config' not in globals():
        st.error("Core application components could not be loaded. The application cannot start.")
        st.caption("Please check the console output when starting Streamlit for import error details.")
    else:
        main()