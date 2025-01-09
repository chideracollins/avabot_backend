from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

from avabot_backend.tools import (
    get_products_for_display,
    search_products,
)


class AvabotAgent:
    _ai_role = """You are a sales representative for an online shopping mobile app, called 'Avabot', and you should act like a sales representative would act. 
    The goal of Avabot is to simplify shopping, making it easy for users to find what they need through conversations with you, rather than having to browse through multiple catalogues and make use of filters and product search bar, as is the case in traditional e-commerce and shopping platforms. 
    Here's a list of the product categories we sell: ['beauty', 'fragrances', 'furniture', 'groceries', 'home-decoration', 'kitchen-accessories', 'laptops', 'mens-shirts', 'mens-shoes', 'mens-watches', 'mobile-accessories', 'motorcycle', 'skin-care', 'smartphones', 'sports-accessories', 'sunglasses', 'tablets', 'tops', 'vehicle', 'womens-bags', 'womens-dresses', 'womens-jewellery', 'womens-shoes', 'womens-watches']. 
    User has two ways of interacting with you, through text and image. If user enquires about our product offerings, make sure to use the neccessary tools at your disposal to find what's available in store before replying user (note: User must not be explicit in his or her request. for example, user may have an event upcoming and needs suggestions on what to get for the event, you can go ahead and make suggestions to user based on what you think user may find interesting. In order to understand what user may find interesting, you can openly ask user, only when necessary, or infer, other times). 
    If user wants to learn about Avabot, do kindly explain to user what Avabot is. 
    Always make sure you are rightfully replying user's requests that is inline with what Avabot is and what it offers, otherwise politely decline the request, however, before doing this, make sure that you have verified that Avabot can't be of help to such request and that not even suggestions to the user of what's available in store can help. 
    Be as persuasive as possible, but also recognize where to stop persuading. After each successful database search using the 'search_products' tool for available products, make sure to display them using the 'get_products_for_display' tool to user immediately, without asking user for permission. 
    Always use tools when necessary. """

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

    _model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-002")

    _tools = [
        get_products_for_display,
        search_products,
    ]

    @classmethod
    def _create_agent_executor(cls, add_image=False):
        if add_image:
            _prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", cls._system_message),
                    MessagesPlaceholder("chat_history", optional=True),
                    (
                        "human",
                        [
                            {"type": "text", "text": cls._human_message},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/jpeg;base64,{image_data}",
                                },
                            },
                        ],
                    ),
                ]
            )
        else:
            _prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", cls._system_message),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", cls._human_message),
                ]
            )

        agent = create_structured_chat_agent(
            llm=cls._model, tools=cls._tools, prompt=_prompt
        )
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=cls._tools,
            verbose=True,
            handle_parsing_errors=True,
        )
        return agent_executor

    @classmethod
    def chat(cls, id, chat_history, message, image_url):
        import httpx
        from PIL import Image

        import base64
        from io import BytesIO

        from avabot_backend.tools import get_retrieved_products

        if image_url:
            image = httpx.get(image_url)

            try:
                image.raise_for_status()
            except:
                return (
                    "Sorry, the attached image file cannot be accessed.",
                    get_retrieved_products(id),
                    chat_history,
                )

            with Image.open(BytesIO(image.content)) as img:
                max_size = (100, 100)
                img.thumbnail(max_size)

                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)

            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

            agent_input = {
                "input": message,
                "image_data": image_base64,
                "chat_history": chat_history,
            }
            response = cls._create_agent_executor(True).invoke(agent_input)
        else:
            agent_input = {
                "input": message,
                "chat_history": chat_history,
            }
            response = cls._create_agent_executor().invoke(agent_input)

        chat_history.append(HumanMessage(message))
        chat_history.append(AIMessage(response["output"]))

        return response["output"], get_retrieved_products(id), chat_history


if __name__ == "__main__":
    print(
        AvabotAgent.chat(
            "test",
            [],
            "Do you sell this?",
            "https://upload.wikimedia.org/wikipedia/commons/4/41/Sunflower_from_Silesia2.jpg",
        )
    )
    
    # 
    # print(
    #     AvabotAgent.chat(
    #         "test",
    #         [],
    #         "What do you sell?",
    #         None,
    #     )
    # )
