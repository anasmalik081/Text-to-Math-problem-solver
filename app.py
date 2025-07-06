import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMMathChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent, Tool
from langchain.callbacks import StreamlitCallbackHandler

# Set Up Streamlit App
st.set_page_config(page_title="Text to Math problem solver and Data Search Assistant", page_icon="📝")
st.title("📝 Text to Math problem solver using Gemma2")

# Sidebar Config
st.sidebar.title("Settings")
API_KEY = st.sidebar.text_input("Enter GROQ API Key", type="password")
if not API_KEY:
    st.info("Please add your GROQ API Key")
    st.stop()

# Load Model
os.environ["GROQ_API_KEY"] = API_KEY
model = ChatGroq(model="gemma2-9b-it")

# Initializing Tools
wrapper = WikipediaAPIWrapper()
wiki_tool = Tool(
    name="Wikipedia",
    func=wrapper.run,
    description="A tool for searching the internet to find various information on the topic mentioned"
)

# Initializing the math tool
math_chain = LLMMathChain.from_llm(llm=model)
calculator = Tool(
    name="Calculator",
    func=math_chain.run,
    description="A tool for answerig math related questions. Only inputs mathematical expression need to be provided"
)

# Prompt
template = (
    """
    You are an Agent tasked for solving user's mathematical questions. Logically arrive at the solution and provide a detailed explaination
    and display it point wise for the question below:
    Question: {question}
    """
)
prompt = PromptTemplate(
    input_variables=["question"],
    template=template
)

# Combine all the tools into chain
chain = LLMChain(
    llm=model,
    prompt=prompt
)
reasoning_tool = Tool(
    name="Reasoning Tool",
    func=chain.run,
    description="A tool for answering logic-based and reasoning questions."
)

# Initialize Agent
assistant_agent = initialize_agent(
    tools=[wiki_tool, calculator, reasoning_tool],
    llm=model,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

# Session State
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I am a Math chatbot who can answer all you maths questions."}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Lets start the interaction
question = st.text_area("Enter your question: ", "I have 5 bananas and 7 grapes. I eat 2 bananas and give away 3 grapes. Then I buy a dozen apples and 2 packs of blueberries. Each pack of blueberries contain 25 berries. How many total pieces of fruit do I have at the end ?")

if st.button("Find my answer"):
    if question:
        with st.spinner("Generate response..."):
            st.session_state.messages.append({"role": "user", "content": question})
            st.chat_message("user").write(question)

            callback = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            response = assistant_agent.run(st.session_state.messages, callbacks=[callback])

            st.session_state.messages.append({'role': "assistant", "content": response})
            st.write("### Response:")
            st.success(response)
    else:
        st.warning("Please enter your question.")