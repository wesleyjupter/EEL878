from socket import *
import streamlit as st 
import os
import time
import random

SIZE = 100000
FORMAT = 'utf-8'
serverName = '127.0.0.1'
serverPort = 12000
addr = (serverName,serverPort)
clientSocket = socket(AF_INET, SOCK_DGRAM)

tempDir = r'auxiliar'

def findChecksum(SentMessage, k):
    SentMessage = SentMessage.encode(FORMAT)

    # Dividindo mensagem em pacotes de k bits
    c1 = SentMessage[0:k]
    c2 = SentMessage[k:2*k]
    c3 = SentMessage[2*k:3*k]
    c4 = SentMessage[3*k:4*k]
 
    # Calculando o binário da soma dos pacotes
    Sum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+int(c4, 2))[2:]
 
    # Adicionando os bits de overflow
    if(len(Sum) > k):
        x = len(Sum)-k
        Sum = bin(int(Sum[0:x], 2)+int(Sum[x:], 2))[2:]
    if(len(Sum) < k):
        Sum = '0'*(k-len(Sum))+Sum
 
    # Calculando o complemento da soma
    Checksum = ''
    for i in Sum:
        if(i == '1'):
            Checksum += '0'
        else:
            Checksum += '1'
    return Checksum

def sendBigPackets(file_path, conn, addr):
    
    # with open(file_path, 'r') as f:
    f = open(file_path,'r')
    data = f.read()
    print(data)
    file_size = len(data)
    qtde_pacotes = (file_size // SIZE)
    qtde_pacotes += 1 if file_size % SIZE != 0 else 0 # soma 1 se length // limit não for uma divisão exata 
    
    msg_binaria = ''.join(format(ord(x), 'b') for x in data)
    checksum = findChecksum(msg_binaria, int(len(msg_binaria)/4))
    
   
    msg = f'1-{qtde_pacotes}-{file_name.name}-{checksum}-0@Null'
    
    verif = '0'
    clientSocket.settimeout(2)
    verif = noLossSendto(msg, clientSocket, verif, addr)
    # conn.sendto(msg.encode(FORMAT), addr) 
    time.sleep(0.1)

    if qtde_pacotes == 1:
        conn.sendto(data.encode(FORMAT), addr)
        time.sleep(0.01)
    else:    
        i = 0
        for index in range(qtde_pacotes - 1):
            inicio = SIZE * index
            fim = inicio + SIZE
            pacote = data[inicio: fim] # divide em pacotes
            
            conn.sendto(pacote.encode(FORMAT), addr)
            time.sleep(0.01)
            i = index

        pacote = data[(i+1)*SIZE:]
        conn.sendto(pacote.encode(FORMAT), addr)

    print("Big packet sended")

#--------------------------------------------------------------------------------------------------

def noLossSendto(msg, conn, verif, addr): #verif do tipo str para verificação do ack
    conn.settimeout(1)
    ack = ''
    while ack != 'ack'+verif:
        print("no loop de sendTO")
        print("ack e verify", ack, verif)
        msg_ack = verif + msg
        if random.random() < 0.9:
            #simulará um pacote enviado sem perda na rede:
            conn.sendto(msg_ack.encode(FORMAT), addr)
            print (f'pacote{verif} enviado')
        else:
            #esse trecho simula um pacote enviado que se perdeu na rede
            print (f'pacote{verif} perdido na rede')

        try:
            ack, addr = conn.recvfrom(SIZE)
            ack = ack.decode(FORMAT)

            print (ack + ' recebido')            
            if verif == '0':
                verif = int(verif) + 1
            else:
                verif = int(verif) - 1
            return str(verif)
        except:
            pass

#--------------------------------------------------------------------------------------------------

def noLossRecv(conn, verif): #verif do tipo int para verificação do ack
    conn.settimeout(1000)
    pacote = ''
    while pacote == '':
        print("no loop de recv")
        pacote, addr = conn.recvfrom(SIZE)
        print("recebi o pacote")
        pacote = pacote.decode(FORMAT)

        # message, addr = serverSocket.recvfrom(SIZE)
        verifR = pacote[0] #verifR eh uma string '0' ou '1'
        
        print(verif, verifR)
        if f'{verif}' == verifR: 
            # o ack de antes foi enviado/recebido
            ack = 'ack'+ verifR

            if random.random() < 0.9:
                # simulará um ack enviado sem perda na rede:
                conn.sendto(ack.encode(FORMAT), addr)
                print (f'{ack} enviado')
            else:
                # esse trecho simula um ack que se perdeu na rede:
                print (f'{ack} perdido na rede')
            
            if verif == '0':
                verifR = int(verifR) + 1
            else:
                verifR = int(verifR) - 1

                conn.sendto("fim!".encode(FORMAT), addr)
            return pacote, str(verifR), addr
        else:
            #o ack de antes não foi enviado/recebido
            pacote = '' #o pacote recebido agora já foi recebido antes
            if verif == '0':
                ack = 'ack'+'1'
            else:
                ack = 'ack'+'0'
            if random.random() < 0.9:
                #simulará um ack enviado sem perda na rede:
                conn.sendto(ack.encode(FORMAT), addr)
                print (f'{ack} enviado')
            else:
                #esse trecho simula um ack que se perdeu na rede:
                print (f'{ack} perdido na rede')


st.set_page_config(layout="wide")
st.title("""Página do Aluno""")
st.subheader("""Busca de notas""")

dre = st.text_input('Digite seu DRE')
grade = st.selectbox('Qual nota gostaria de saber?', ['P1', 'P2','Trabalho', 'Média Final'])
button = st.button('Buscar nota')

verif = '0'
if button:
    #Sending info
    message = f'{dre}-{grade}'
    message = f'0-{message}'

    clientSocket.settimeout(2)
    verif = noLossSendto(message, clientSocket, verif, addr)
    print("esperando mensagem")
    message, verif, addr = noLossRecv(clientSocket, verif)
    message = message[1:]
    print("recebi mensagem")


    # clientSocket.sendto(message.encode(FORMAT) , addr)
    # modifiedMessage, serverAddress = clientSocket.recvfrom(SIZE)

    st.write(message)
    
    if grade == 'Média Final':
       st.write('Forma de Cálculo da Média Final')
       r'''
       $$MF = \frac{P1+P2}{2} \times 0,8 + Trabalho \times 0,2$$
       '''
    
#----------------------------------------------------------------------------------------------------------------------

file_name = st.file_uploader('Upload do trabalho (arquivo txt - 1 arquivo por vez)', accept_multiple_files = False)
button2 = st.button('Enviar trabalho')

if button2:
    with open(os.path.join(tempDir, file_name.name),"wb") as f:
        f.write(file_name.getbuffer())

        file_path = os.path.join(tempDir, file_name.name)
    
    print(file_path)
    sendBigPackets(file_path, clientSocket, addr)
        
   