import openai
import yaml
from time import time, sleep
from uuid import uuid4


def save_yaml(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()
    
    
def format_messages(conversations):
    # Check if conversations is a list
    if not isinstance(conversations, list):
        raise ValueError("Expected a list of conversations")

    all_messages = []
    for conversation in conversations:
        # Check if each 'conversation' is a dictionary
        if not isinstance(conversation, dict):
            raise ValueError("Each conversation should be a dictionary")
            
        role = conversation.get("role", "").upper()
        content = conversation.get("content", "")
        
        # Additional check for role and content types, if needed
        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError("Role and Content should be of type str")

        message = f"{role}: {content}"
        all_messages.append(message)

    return all_messages


def keep_recent_items(lst, num_to_keep):
    return lst[-num_to_keep:]

def extract_user_messages(conversations):
    user_messages = []
    for conversation in conversations:
        if conversation.get("role") == 'user':
            content = conversation.get("content", "").strip()  # strip() is used to remove leading and trailing whitespaces
            user_messages.append(content)
    return user_messages



def chatbot(messages, model="gpt-4", temperature=0):
    max_retry = 7
    retry = 0
    while True:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
            text = response['choices'][0]['message']['content']
            
            # ###    trim message object
            # debug_object = [i['content'] for i in messages]
            # debug_object.append(text)
            # save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
            if response['usage']['total_tokens'] >= 7000:
                a = messages.pop(1)
            
            return text
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            if 'maximum context length' in str(oops):
                a = messages.pop(1)
                print('\n\n DEBUG: Trimming oldest message')
                continue
            retry += 1
            if retry >= max_retry:
                print(f"\n\nExiting due to excessive errors in API: {oops}")
                exit(1)
            print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)




def main(conversation,current_profile,kb="No KB articles yet",api_key=0):
    print(type(conversation))

    all_messages = format_messages(conversation)
    all_messages = keep_recent_items(all_messages,5)
    print(all_messages)
    user_messages= extract_user_messages(conversation)
    user_messages = keep_recent_items(user_messages,3)
    

    # instantiate chatbot
    openai.api_key = api_key
    # conversation = list()
    # conversation.append({'role': 'system', 'content': open_file('system_default.txt')})
    # user_messages = list()
    # all_messages = list()
    
    while True:
        # get user input
        print(conversation)
        #text = user_messages[-1]
        #print(text)
        #save_file('chat_logs/chat_%s_user.txt' % time(), text)


        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()

        
        # search KB, update default system
        default_system = open_file('system_default.txt').replace('<<PROFILE>>', current_profile).replace('<<KB>>', kb)
        #print('SYSTEM: %s' % default_system)
        conversation[0]['content'] = default_system


        # generate a response
        response = chatbot(conversation)
        #save_file('chat_logs/chat_%s_chatbot.txt' % time(), response)
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('CHATBOT: %s' % response)
        print('\n\nCHATBOT: %s' % response)


        # update user scratchpad
        if len(user_messages) > 3:
            user_messages.pop(0)
        user_scratchpad = '\n'.join(user_messages).strip()


        # update user profile
        print('\n\nUpdating user profile...')
        profile_length = len(current_profile.split(' '))
        profile_conversation = list()
        profile_conversation.append({'role': 'system', 'content': open_file('system_update_user_profile.txt').replace('<<UPD>>', current_profile).replace('<<WORDS>>', str(profile_length))})
        profile_conversation.append({'role': 'user', 'content': user_scratchpad})
        profile = chatbot(profile_conversation)


        # update main scratchpad
        if len(all_messages) > 5:
            all_messages.pop(0)
        main_scratchpad = '\n\n'.join(all_messages).strip()


        # Update the knowledge base
        print('\n\nUpdating KB...')
        if len(all_messages) == 0:
            # yay first KB!
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('system_instantiate_new_kb.txt')})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
        else:     
            # Expand current KB
            kb_convo = list()
            kb_convo.append({'role': 'system', 'content': open_file('system_update_existing_kb.txt').replace('<<KB>>', kb)})
            kb_convo.append({'role': 'user', 'content': main_scratchpad})
            article = chatbot(kb_convo)
    
            # Split KB if too large
            kb_len = len(article.split(' '))
            if kb_len > 1000:
                kb_convo = list()
                kb_convo.append({'role': 'system', 'content': open_file('summarize.txt')})
                kb_convo.append({'role': 'user', 'content': article})
                article = chatbot(kb_convo)

        print(all_messages)
        print(user_messages)
        return response, conversation, profile, article