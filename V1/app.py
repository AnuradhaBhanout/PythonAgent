import streamlit as st
import uuid
import agent  # Import our agent configurations

# Page Configuration
st.set_page_config(page_title="Essay Workspace", layout="wide")

# Persistent state initialization so clicking different tabs doesn't wipe current data
if "task" not in st.session_state:
    st.session_state.task = "Pizza Shop"
if "plan" not in st.session_state:
    st.session_state.plan = ""
if "content" not in st.session_state:
    st.session_state.content = []
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "critique" not in st.session_state:
    st.session_state.critique = ""
if "snapshots" not in st.session_state:
    st.session_state.snapshots = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "revision_number" not in st.session_state:
    st.session_state.revision_number = 1
if "max_revisions" not in st.session_state:
    st.session_state.max_revisions = 2

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Workspace Settings")
    
    # Fast models speed up API runs drastically
    selected_model = st.selectbox(
        "Choose Model (Use fast models to resolve 7-min bottleneck)",
        options=[
            "poolside/laguna-m.1:free", 
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.5-flash",
            "openai/gpt-4o-mini"
        ],
        index=1  # Defaults to Llama-3.3-70b-instruct:free (highly responsive)
    )
    # Inject model name back to the agent script
    agent.SELECTED_MODEL_NAME = selected_model
    
    max_revs = st.slider("Maximum Revisions Allowed", min_value=1, max_value=5, value=st.session_state.max_revisions)
    st.session_state.max_revisions = max_revs

# Dynamic Tabs Setup
tab_agent, tab_plan, tab_research, tab_draft, tab_critique, tab_snapshots = st.tabs([
    "📂 Agent", "📋 Plan", "🔍 Research Content", "📝 Draft", "🧐 Critique", "🎞️ StateSnapShots"
])

# 1. AGENT TAB
with tab_agent:
    st.subheader("Agent Configuration & Execution Panel")
    
    task_input = st.text_input("Essay Topic", value=st.session_state.task)
    st.session_state.task = task_input

    col1, col2 = st.columns(2)
    with col1:
        generate_clicked = st.button("Generate Essay", type="primary", use_container_width=True)
    with col2:
        continue_clicked = st.button("Continue Essay", use_container_width=True)

    # Reusable workflow execution loop
    def run_agent_workflow(resume=False):
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        if resume:
            inputs = None
            # Update graph settings in the checkpoint before starting resumption runs
            agent.graph.update_state(
                config, 
                {"max_revisions": st.session_state.max_revisions}, 
                as_node="generate"
            )
        else:
            inputs = {
                'task': st.session_state.task,
                "max_revisions": st.session_state.max_revisions,
                "revision_number": 1,
                "content": []
            }
            
        status_placeholder = st.empty()
        
        with status_placeholder.status("Executing Multi-Agent Graph...", expanded=True) as status:
            for event in agent.graph.stream(inputs, config):
                for node, state_update in event.items():
                    status.update(label=f"Active Node processing: {node.upper()}")
                    
                    # Store results in Session State
                    if "plan" in state_update:
                        st.session_state.plan = state_update["plan"]
                    if "content" in state_update:
                        st.session_state.content = state_update["content"]
                    if "draft" in state_update:
                        st.session_state.draft = state_update["draft"]
                    if "critique" in state_update:
                        st.session_state.critique = state_update["critique"]
                    if "revision_number" in state_update:
                        st.session_state.revision_number = state_update["revision_number"]

                    # Append checkpoint snapshot for the StateSnapShots tab
                    st.session_state.snapshots.append({
                        "node": node,
                        "plan": st.session_state.plan,
                        "draft": st.session_state.draft,
                        "critique": st.session_state.critique,
                        "revision_number": st.session_state.revision_number
                    })
                    
            status.update(label="All agent stages completed successfully!", state="complete", expanded=False)
        st.rerun()

    # Trigger fresh generation execution
    if generate_clicked:
        st.session_state.plan = ""
        st.session_state.content = []
        st.session_state.draft = ""
        st.session_state.critique = ""
        st.session_state.snapshots = []
        st.session_state.revision_number = 1
        st.session_state.thread_id = str(uuid.uuid4())
        
        run_agent_workflow(resume=False)

    # Continue execution (resume workflow where it paused)
    if continue_clicked:
        st.session_state.max_revisions += 1
        run_agent_workflow(resume=True)

# 2. PLAN TAB
with tab_plan:
    st.subheader("High-Level Outline & Strategy")
    if st.session_state.plan:
        st.markdown(st.session_state.plan)
    else:
        st.info("No plan draft loaded. Navigate to the 'Agent' tab to start execution.")

# 3. RESEARCH CONTENT TAB
with tab_research:
    st.subheader("Gathered Search Intelligence")
    if st.session_state.content:
        for idx, text in enumerate(st.session_state.content):
            with st.expander(f"Reference Source Material #{idx+1}", expanded=True):
                st.write(text)
    else:
        st.info("No sources retrieved yet.")

# 4. DRAFT TAB
with tab_draft:
    st.subheader("Current Working Draft")
    if st.session_state.draft:
        st.markdown(st.session_state.draft)
    else:
        st.info("No draft compiled yet.")

# 5. CRITIQUE TAB
with tab_critique:
    st.subheader("System Editorial Assessment")
    if st.session_state.critique:
        st.markdown(st.session_state.critique)
    else:
        st.info("No audit feedback generated yet.")

# 6. STATE SNAPSHOTS TAB
with tab_snapshots:
    st.subheader("Step-by-Step Workflow Transitions")
    if st.session_state.snapshots:
        for idx, snap in enumerate(st.session_state.snapshots):
            with st.expander(f"Step {idx+1}: Node executed: {snap['node'].upper()} (Revision {snap['revision_number']})"):
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    st.write("**Outline State:**")
                    st.write(snap['plan'][:200] + "..." if snap['plan'] else "Empty")
                    st.write("**Critic Feedback:**")
                    st.write(snap['critique'][:200] + "..." if snap['critique'] else "Empty")
                with col_sub2:
                    st.write("**Essay Draft Content:**")
                    st.write(snap['draft'][:400] + "..." if snap['draft'] else "Empty")
    else:
        st.info("No structural execution traces logged.")