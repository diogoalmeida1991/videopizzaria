import requests
import json
import re
import time
import subprocess #integração de ambiente com outras bibliotecas

#To clean unwanted text as what is before "Atendente".
def clean_response(response):
    if re.search("Atendente:", response) != None:
        text = no_atendente(response)
        return "Atendente: " + text
    else:
        return response
        
def no_atendente(response):        
    text = response.split("Atendente:", 1)[-1].strip()
    return text

#To remove text /n         
def clean_jumpline(response):
    response = response.replace("\n", " ")
    response = response.replace("(", " ")
    response = response.replace(")", " ")
    response = no_atendente(response)
    return response
    
url = "http://localhost:11434/api/generate" #With Ollama opened use your localhost (127.0.0.1) port 11434 to host it.

headers = {
    "Content-Type": "application/json" #This is API json comunication
}

brain = open('brain.txt', encoding = 'utf-8', errors = 'ignore').read()
brain = re.sub(r'\n', ' ', brain)

data = {
    "model": "llama3.1:70b",
    "prompt": "Eu gostaria de simular uma conversa entre um atendente de pizzaria e um cliente baseado no seguinte texto e regras: '" + brain + "' você será o atendente e eu o cliente, toda conversa que você iniciar deve começar com 'Atendente:' e você deve manter o diálogo até eu me despedir, entendeu?",
    "stream": False,
    "context": [1,2,3] 
}

#Try for three times
for i in range(0,3):
    start_time = time.perf_counter()
    response = requests.post(url, headers=headers, data=json.dumps(data)) #the dictionary was send to the server
    result = json.loads(response.text)#the model response was sended to variable result
    data["context"] = result["context"]#Start a memory of a conversation
    #The follow line is a debug with the result, whether this was a success case, this line can to be commented: 
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Tempo Abertura{i}: {execution_time}.")
    if re.search("Atendente:", result["response"]) != None:
        actual_response = clean_response(result["response"])
        print(actual_response)
        actual_response = clean_jumpline(actual_response)
        subprocess.run('conda run -n audio-webui python criaaudio.py --text "' + actual_response + '"', shell=True)
        subprocess.run('conda run -n wav2lip python inference.py --checkpoint_path checkpoints/wav2lip.pth --face modelo.mp4 --audio audio.wav', shell=True)
        break

#The loop with interation with the user
while True:
    #if unsuccessful in initial conversation, stop the while
    if i >= 2:
        print("Eu não estou entendendo suas regras")
        print(result["response"])
        break
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Tempo de execução: {execution_time}.")
    data["prompt"] = input("Cliente: ")#User do the ask
    start_time = time.perf_counter()
    if(data["prompt"] == ""): #Ignore void strings (this can to be used to avoid injection attacks)
        print("Digite uma pergunta valida")
    else:
        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:#If the response was 200 (success) do:
            response = json.loads(response.text)
            actual_response = clean_response(response["response"])
            data["context"] = response["context"]#Mantain a memory of a conversation
            if re.search("Atendente:", actual_response) == None:
                print("***erro*** " +  actual_response + "***erro***")
                data["prompt"] = "Lembre-se de simular uma conversa entre um atendente de pizzaria e um cliente baseado no seguinte texto e regras: '" + brain + "' onde você será o atendente e eu o cliente, toda conversa que você iniciar deve começar com 'Atendente:'."
                response = requests.post(url, headers=headers, data=json.dumps(data))
                response = json.loads(response.text)
                actual_response = clean_response(response["response"])
                data["context"] = response["context"]#Mantain a memory of a conversation
                
                print(actual_response)
                actual_response = clean_jumpline(actual_response)
                subprocess.run('conda run -n audio-webui python criaaudio.py --text "' + actual_response + '"', shell=True)
                subprocess.run('conda run -n wav2lip python inference.py --checkpoint_path checkpoints/wav2lip.pth --face modelo.mp4 --audio audio.wav', shell=True)
            else:
                print(actual_response)
                actual_response = clean_jumpline(actual_response)
                subprocess.run('conda run -n audio-webui python criaaudio.py --text "' + actual_response + '"', shell=True)
                subprocess.run('conda run -n wav2lip python inference.py --checkpoint_path checkpoints/wav2lip.pth --face modelo.mp4 --audio audio.wav', shell=True)
        else:
            print("Error:", response.status_code, response.text)