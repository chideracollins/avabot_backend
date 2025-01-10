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

    _prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _system_message),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", _human_message),
        ]
    )

    _agent = create_structured_chat_agent(llm=_model, tools=_tools, prompt=_prompt)

    _agent_executor = AgentExecutor.from_agent_and_tools(
        agent=_agent,
        tools=_tools,
        verbose=True,
        handle_parsing_errors=True,
    )

    @classmethod
    def _download_and_resize_image(cls, image_url):
        import httpx
        from PIL import Image

        import base64
        from io import BytesIO

        image = httpx.get(image_url)

        try:
            image.raise_for_status()
        except:
            return

        with Image.open(BytesIO(image.content)) as img:
            max_size = (100, 100)
            img.thumbnail(max_size)

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return image_base64

    @classmethod
    def _create_better_user_prompt(cls, message, image_url):
        image_base64 = cls._download_and_resize_image(image_url)

        if image_base64 is None:
            return

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are being provided with a user question, which includes an image. Understand it and provide a response that articulates clearly what the user is asking about. Always leave your response in a first person perspective, (i.e. let your response look like you are the person that asked the question initially, just that this time, you posed a more clear question, that captures the user's intent.)",
                ),
                (
                    "human",
                    [
                        {"type": "text", "text": message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                    ],
                ),
            ]
        )

        response = cls._model.invoke(prompt)
        return response.content

    @classmethod
    def _create_chat_history(history: dict):
        chat_history = []
        
        for key, value in history.items():
            chat_history.append(HumanMessage(key))
            chat_history.append(AIMessage(value))
            
        return chat_history

    @classmethod
    def chat(cls, id, history, message, image_url):
        from avabot_backend.tools import get_retrieved_products

        if image_url:
            message = cls._create_better_user_prompt(message, image_url)

            if message is None:
                return (
                    "Sorry, the attached image file cannot be accessed.",
                    None,
                    history,
                )

        if history:
            agent_input = {
                "input": message,
                "chat_history": cls._create_chat_history(history),
            }
        else:
            history = {}
            agent_input = {
                "input": message,
            }

        response = cls._agent_executor.invoke(agent_input)

        products = get_retrieved_products(id)

        history[message] = response["output"] + f"Attached products: {products}"

        return response["output"], products, history


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
