from langchain.chat_models import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate
)
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

class ChatGPTEngine:
    def __init__(self):
        self.llm = ChatOpenAI()
        # self.messages = []

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

        self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
        self.chain = ConversationChain(memory=self.memory, prompt=prompt, llm=self.llm)

    def query(self, message):
        try:
            return self.chain.predict(input=message)
        except Exception as e:
            return str(e)