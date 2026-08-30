"""
Skylark Drones BI Agent - Streamlit UI
Conversational interface for business intelligence queries
"""
import streamlit as st
import logging
from datetime import datetime
from typing import Optional

from app.config import Config
from app.monday_client import MondayClient, MondayAPIError
from app.agent import Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Skylark Drones BI Agent",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-good {
        color: #28a745;
    }
    .status-warning {
        color: #ffc107;
    }
    .status-error {
        color: #dc3545;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.connection_status = "Not checked"
    st.session_state.messages = []

if "config_validated" not in st.session_state:
    st.session_state.config_validated = False


def initialize_agent():
    """Initialize the agent and test connection"""
    try:
        monday_client = MondayClient()
        connection_ok = monday_client.test_connection()
        
        if connection_ok:
            st.session_state.agent = Agent(monday_client)
            st.session_state.connection_status = "✅ Connected"
            st.session_state.config_validated = True
            return True
        else:
            st.session_state.connection_status = "❌ Connection failed"
            return False
    except Exception as e:
        st.session_state.connection_status = f"❌ Error: {str(e)}"
        logger.error(f"Failed to initialize agent: {e}")
        return False


def render_sidebar():
    """Render sidebar with configuration and status"""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Validate config
        is_valid, missing = Config.validate()
        
        if not is_valid:
            st.error(f"Missing configuration: {', '.join(missing)}")
            st.info(
                "Please set the following environment variables:\n"
                "- MONDAY_API_TOKEN\n"
                "- DEALS_BOARD_ID\n"
                "- WORK_ORDERS_BOARD_ID\n"
                "- OPENAI_API_KEY"
            )
            return False
        
        # Show safe config
        config_display = Config.get_safe_config_display()
        
        with st.expander("📋 Configuration Details"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Deals Board", config_display["deals_board_id"])
            with col2:
                st.metric("Work Orders Board", config_display["work_orders_board_id"])
        
        st.markdown("---")
        st.markdown("## 🔗 Status")
        
        if st.button("🔄 Test Connection", key="test_connection"):
            with st.spinner("Testing Monday.com connection..."):
                if initialize_agent():
                    st.success("✅ Connected to Monday.com successfully!")
                else:
                    st.error("❌ Connection failed. Check your API token.")
        
        st.markdown(f"**Status:** {st.session_state.connection_status}")
        
        st.markdown("---")
        st.markdown("## 💡 Example Questions")
        
        examples = [
            "How's our pipeline looking this quarter?",
            "What's our total active pipeline?",
            "Which sectors have the strongest pipeline?",
            "How much revenue did we generate?",
            "Which work orders are delayed?",
            "Compare energy and manufacturing performance",
            "Give me a leadership update",
        ]
        
        for example in examples:
            if st.button(f"➡️ {example}", key=f"example_{example[:20]}"):
                st.session_state.messages.append(("user", example))
                st.rerun()
        
        st.markdown("---")
        st.markdown("## 📊 About")
        st.markdown(
            "This BI agent answers business questions using data from:\n"
            "- **Deals board**: Sales pipeline tracking\n"
            "- **Work Orders board**: Project execution and billing"
        )


def render_main():
    """Render main chat interface"""
    st.markdown(
        "<h1 class='main-header'>🚁 Skylark Drones Business Intelligence Agent</h1>",
        unsafe_allow_html=True,
    )
    
    # Check if config is valid
    is_valid, missing = Config.validate()
    if not is_valid:
        st.error(
            f"⚠️ Configuration incomplete. Missing: {', '.join(missing)}\n\n"
            "Please check the sidebar for setup instructions."
        )
        return
    
    # Ensure agent is initialized
    if st.session_state.agent is None:
        with st.spinner("Initializing connection to Monday.com..."):
            if not initialize_agent():
                st.error("Failed to connect to Monday.com. Check your API configuration.")
                return
    
    # Display connection status
    status_col, refresh_col = st.columns([3, 1])
    with status_col:
        if "✅" in st.session_state.connection_status:
            st.markdown(
                f"<p class='status-good'>{st.session_state.connection_status}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<p class='status-error'>{st.session_state.connection_status}</p>",
                unsafe_allow_html=True,
            )
    
    # Chat history
    st.markdown("---")
    
    if not st.session_state.messages:
        st.info("👋 Hello! Ask me about your pipeline, revenue, work orders, or business performance.")
    
    # Display chat messages
    for role, content in st.session_state.messages:
        with st.chat_message(role):
            if isinstance(content, str):
                st.markdown(content)
            elif isinstance(content, dict):
                # Display structured response with metrics
                if "response" in content:
                    st.markdown(content["response"])
                
                if "analysis" in content and content["analysis"]:
                    with st.expander("📊 Detailed Analysis"):
                        for key, value in content["analysis"].items():
                            st.write(f"**{key}:** {value}")
                
                if "caveats" in content and content["caveats"]:
                    with st.expander("⚠️ Data Quality Notes"):
                        for caveat in content["caveats"]:
                            st.warning(caveat)
    
    # Input area
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.chat_input("Ask me about your business...")
    
    with col2:
        if st.button("📈 Leadership Update", key="leadership_btn"):
            user_input = "Generate a leadership update"
    
    # Process user input
    if user_input:
        # Add user message to history
        st.session_state.messages.append(("user", user_input))
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Check for leadership update request
        if any(word in user_input.lower() for word in ["leadership", "executive", "update", "summary"]):
            with st.spinner("Generating leadership update..."):
                try:
                    summary_result = st.session_state.agent.generate_leadership_summary()
                    
                    if summary_result.get("success"):
                        summary = summary_result.get("summary", {})
                        
                        response_text = "## Leadership Summary\n\n"
                        
                        # Pipeline section
                        if "pipeline" in summary:
                            p = summary["pipeline"]
                            response_text += f"""### 💼 Pipeline Status
- **Total Pipeline Value**: ${p['total_value']:,.0f} ({p['total_count']} deals)
- **Active Pipeline**: ${p['active_value']:,.0f} ({p['active_count']} deals)
- **Average Deal Size**: ${p.get('average_deal_size', 0):,.0f}
"""
                        
                        # Work Orders section
                        if "work_orders" in summary:
                            wo = summary["work_orders"]
                            response_text += f"""### 📋 Work Orders
- **Active**: {wo['active_count']} projects in progress
- **Completed**: {wo['completed_count']} projects finished
- **Delayed**: {wo['delayed_count']} projects overdue
- **Total Billed**: ${wo['total_billed']:,.0f}
"""
                        
                        # Sector performance
                        if "by_sector" in summary:
                            response_text += "\n### 📊 Performance by Sector\n"
                            
                            if summary["by_sector"].get("pipeline"):
                                response_text += "\n**Pipeline by Sector:**\n"
                                for sector, (value, count) in sorted(
                                    summary["by_sector"]["pipeline"].items(),
                                    key=lambda x: x[1][0],
                                    reverse=True
                                )[:5]:  # Top 5
                                    response_text += f"- {sector}: ${value:,.0f}\n"
                        
                        # Data quality notes
                        if summary.get("data_quality_caveats"):
                            response_text += "\n### ⚠️ Data Quality Notes\n"
                            for issue in summary["data_quality_caveats"]:
                                response_text += f"- {issue}\n"
                        
                        # Add to history and display
                        response_obj = {
                            "response": response_text,
                            "analysis": summary,
                            "caveats": summary.get("data_quality_caveats", []),
                        }
                        st.session_state.messages.append(("assistant", response_obj))
                        
                        with st.chat_message("assistant"):
                            st.markdown(response_text)
                            
                            if summary.get("data_quality_caveats"):
                                with st.expander("⚠️ Data Quality Notes"):
                                    for caveat in summary["data_quality_caveats"]:
                                        st.info(caveat)
                    else:
                        error_msg = "Failed to generate leadership update."
                        st.session_state.messages.append(("assistant", error_msg))
                        with st.chat_message("assistant"):
                            st.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.session_state.messages.append(("assistant", error_msg))
                    with st.chat_message("assistant"):
                        st.error(error_msg)
                    logger.error(f"Leadership update error: {e}")
        
        else:
            # Regular query
            with st.spinner("Analyzing your question..."):
                try:
                    result = st.session_state.agent.execute_query(user_input)
                    
                    if result.get("success"):
                        if result.get("type") == "clarification":
                            response_text = result.get("message", "")
                        else:
                            response_text = result.get("response", "")
                        
                        response_obj = {
                            "response": response_text,
                            "analysis": result.get("analysis", {}),
                            "caveats": result.get("caveats", []),
                        }
                        st.session_state.messages.append(("assistant", response_obj))
                        
                        with st.chat_message("assistant"):
                            st.markdown(response_text)
                            
                            if result.get("analysis"):
                                with st.expander("📊 Detailed Analysis"):
                                    for key, value in result.get("analysis", {}).items():
                                        st.write(f"**{key}:** {value}")
                            
                            if result.get("caveats"):
                                with st.expander("⚠️ Data Quality Notes"):
                                    for caveat in result.get("caveats"):
                                        st.info(caveat)
                    else:
                        error_msg = result.get("message", "An error occurred")
                        st.session_state.messages.append(("assistant", error_msg))
                        with st.chat_message("assistant"):
                            st.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.session_state.messages.append(("assistant", error_msg))
                    with st.chat_message("assistant"):
                        st.error(error_msg)
                    logger.error(f"Query execution error: {e}")


def main():
    """Main application entry point"""
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main()


if __name__ == "__main__":
    main()
