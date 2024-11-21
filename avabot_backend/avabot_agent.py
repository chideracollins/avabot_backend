from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from avabot_backend.tools import (
    get_products_for_display,
    search_products,
)


class AvabotAgent:
    _ai_role = "You are a sales representative for an online shopping mobile app, called 'Avabot', and you should act like a sales representative would act. The goal of Avabot is to simplify shopping, making it easy for users to find what they need through conversations with you, rather than having to browse through multiple catalogues and make use of filters and product search bar, as is the case in traditional e-commerce and shopping platforms. Here's a list of the product categories we sell: ['beauty', 'fragrances', 'furniture', 'groceries', 'home-decoration', 'kitchen-accessories', 'laptops', 'mens-shirts', 'mens-shoes', 'mens-watches', 'mobile-accessories', 'motorcycle', 'skin-care', 'smartphones', 'sports-accessories', 'sunglasses', 'tablets', 'tops', 'vehicle', 'womens-bags', 'womens-dresses', 'womens-jewellery', 'womens-shoes', 'womens-watches']. User has two ways of interacting with you, through text and image. If user enquires about our product offerings, make sure to use the neccessary tools at your disposal to find what's available in store before replying user (note: User must not be explicit in his or her request. for example, user may have an event upcoming and needs suggestions on what to get for the event, you can go ahead and make suggestions to user based on what you think user may find interesting. In order to understand what user may find interesting, you can openly ask user, only when necessary, or infer, other times). If user wants to learn about Avabot, do kindly explain to user what Avabot is. Always make sure you are rightfully replying user's requests that is inline with what Avabot is and what it offers, otherwise politely decline the request, however, before doing this, make sure that you have verified that Avabot can't be of help to such request and that not even suggestions to the user of what's available in store can help. Be as persuasive as possible, but also recognize where to stop persuading. After each successful database search using the 'search_products' tool for available products, make sure to display them using the 'get_products_for_display' tool to user immediately, without asking user for permission. Always use tools when necessary. "

    _system_message = (
        _ai_role
        + """Respond to the human as helpfully and accurately as possible. You have access to the following tools:
    
    {tools}

    Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

    Valid "action" values: "Final Answer" or {tool_names}

    Provide only ONE action per $JSON_BLOB, as shown:

    ```
    {{
        "action": $TOOL_NAME,
        "action_input": $INPUT
    }}
    ```

    Follow this format:

    Question: input question to answer
    Thought: consider previous and subsequent steps
    Action:
    ```
    $JSON_BLOB
    ```
    Observation: action result
    ... (repeat Thought/Action/Observation N times)
    Thought: I know what to respond
    Action:
    ```
    {{
        "action": "Final Answer",
        "action_input": "Final response to human"
    }}

    Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation"""
    )

    _human_message = """{input}

    {agent_scratchpad}

    (reminder to respond in a JSON blob no matter what)"""

    _prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _system_message),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", _human_message),
        ]
    )

    _model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

    _tools = [
        get_products_for_display,
        search_products,
    ]

    _agent = create_structured_chat_agent(llm=_model, tools=_tools, prompt=_prompt)
    _agent_executor = AgentExecutor.from_agent_and_tools(
        agent=_agent,
        tools=_tools,
        verbose=True,
        handle_parsing_errors=True,
    )

    agents = []

    def __init__(self, id):
        self._id = id
        self._chat_history = []
        self._products = None
        """Used to keep track of the retrieved products for the current user query - ai reply cycle."""

    @classmethod
    def _get_or_create(cls, agent_id):
        if len(cls.agents) > 0:
            for agent in cls.agents:
                if agent._id == agent_id:
                    return agent

        agent = cls(agent_id)
        cls.agents.append(agent)
        return agent

    @property
    def _get_products(self):
        from avabot_backend.tools import get_retrieved_products

        self._products = get_retrieved_products(self._id)

    def _reply(self, message):
        response = self._agent_executor.invoke(
            {
                "input": message,
                "chat_history": self._chat_history,
            }
        )
        self._get_products
        self._chat_history.append(HumanMessage(message))
        self._chat_history.append(AIMessage(response["output"]))
        print(self._chat_history)
        return response["output"]

    @classmethod
    def chat(cls, user_id, user_message):
        agent = cls._get_or_create(user_id)
        reply = agent._reply(user_message)
        products = agent._products
        agent._products.clear()
        return reply, products



