from socket import *
import pandas as pd
import os
import random 

TEACHER_FOLDER = r'Pasta do Professor'
SIZE = 100000
FORMAT = 'utf-8'
SEPARADOR = '-'
serverName="127.0.0.1"
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
addr = (serverName, serverPort)
print('The server is ready to receive')

def ReceiverChecksum(ReceivedMessage, k):
   
    # Dividindo mensagem em pacotes de k bits
    c1 = ReceivedMessage[0:k]
    c2 = ReceivedMessage[k:2*k]
    c3 = ReceivedMessage[2*k:3*k]
    c4 = ReceivedMessage[3*k:4*k]
 
    #  Calculando o binário da soma dos pacotes
    ReceiverSum = bin(int(c1, 2)+int(c2, 2)+int(c3, 2)+int(c4, 2))[2:]
 
    #  Adicionando os bits de overflow
    if(len(ReceiverSum) > k):
        x = len(ReceiverSum)-k
        ReceiverSum = bin(int(ReceiverSum[0:x], 2)+int(ReceiverSum[x:], 2))[2:]
    if(len(ReceiverSum) < k):
        ReceiverSum = '0'*(k-len(ReceiverSum))+ReceiverSum
 
    # Calculando o complemento da soma
    ReceiverChecksum = ''
    for i in ReceiverSum:
        if(i == '1'):
            ReceiverChecksum += '0'
        else:
            ReceiverChecksum+= '1'
    return ReceiverChecksum

def recebePacoteGrande(conn, qtde_pacotes, file_path, checksum):
    f = open(file_path, 'w')
    pacote = ''
    for _ in range(qtde_pacotes):
        pacote = pacote + conn.recv(SIZE).decode(FORMAT)
        
    pacote_binario = ''.join(format(ord(x), 'b') for x in pacote)
    print("pré checksum")
    receiver_checksum = ReceiverChecksum(pacote_binario, int(len(pacote_binario)/4))
    print("pós checksum")
    confere_checksum = int(receiver_checksum,2)-int(checksum,2)
    
    if(confere_checksum == 0):
        print("Checksum = 0")
        print("STATUS: ACCEPTED | Arquivo Recebido")
        f.write(pacote)

    else:
        print("Checksum <> 0")
        print("STATUS: ERROR DETECTED")

def noLossRecv(conn, verif): #verif do tipo int para verificação do ack
    conn.settimeout(1000)
    pacote = ''
    while pacote == '':

        pacote, clientAddress = conn.recvfrom(SIZE)
        pacote = pacote.decode(FORMAT)
        print(pacote)
        # message, clientAddress = serverSocket.recvfrom(SIZE)
        verifR = pacote[0] #verifR eh uma string '0' ou '1'
        
        print(verif, verifR)
        if f'{verif}' == verifR: 
            # o ack de antes foi enviado/recebido
            ack = 'ack'+ verifR

            if random.random() < 0.9:
                # simulará um ack enviado sem perda na rede:
                conn.sendto(ack.encode(FORMAT), clientAddress)
                print (f'{ack} enviado')
            else:
                # esse trecho simula um ack que se perdeu na rede:
                print (f'{ack} perdido na rede')
            
            if verif == '0':
                verifR = int(verifR) + 1
            else:
                verifR = int(verifR) - 1

            return pacote, str(verifR), clientAddress
        else:
            #o ack de antes não foi enviado/recebido
            pacote = '' #o pacote recebido agora já foi recebido antes
            if verif == '0':
                ack = 'ack'+'1'
            else:
                ack = 'ack'+'0'
            if random.random() < 0.9:
                #simulará um ack enviado sem perda na rede:
                conn.sendto(ack.encode(FORMAT), clientAddress)
                print (f'{ack} enviado')
            else:
                #esse trecho simula um ack que se perdeu na rede:
                print (f'{ack} perdido na rede')
    


def noLossSendto(msg, conn, verif, addr): #verif do tipo str para verificação do ack
    conn.settimeout(1)
    ack = ''
    # while ack != 'ack'+verif:
    verif = str(verif)
    print(verif)
    while ack != 'ack' + str(verif) :
        print("no loop de sendTO")
        print("ack e verify", ack, verif)
        msg_ack = str(verif) + msg
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
            
            if(ack == "fim!"):
                return str(verif)
        except:
            print('timeout: ack não recebido')
            pass

    return str(verif)

verif = '0'
while 1:
    
    # message, verif, clientAddress = serverSocket.recvfrom(SIZE)
    message, verif, clientAddress = noLossRecv(serverSocket, verif)
    message = message[1:]
    print("Messagem recebida: ", message)
    file_type = message.split('-')[0]
    print('file_type', file_type)
    print(message)
    
    if file_type == '0':
        dre = message.split('-')[1]
        prova = message.split('-')[2]

        df = pd.read_excel(os.path.join(TEACHER_FOLDER, 'notas.xlsx'))
        df_ = df[(df['DRE'].apply(str) == dre)].copy()
        if not df_.empty:
            modifiedmessage = 'Sua nota é: '+ str(df_.iloc[0][prova]) 
            verif = noLossSendto(modifiedmessage, serverSocket, verif, clientAddress)
            # serverSocket.sendto(modifiedmessage.encode(FORMAT), clientAddress) 
        else: 
            modifiedmessage = 'Esse DRE não é válido'

            verif = noLossSendto(modifiedmessage, serverSocket, verif, clientAddress)
        
        print("terminei de enviar")
            # serverSocket.sendto(modifiedmessage.encode(FORMAT), clientAddress) 
        verif = '0'

    #-----------------------------------------------------------------------------------------------------------        
    
    elif file_type == '1': 
        #msg = f'1-{qtde_pacotes}-{file_name}-0@Null'
        qtde_pacotes = message.split('-')[1]
        file_name = message.split('-')[2]
        checksum =  message.split('-')[3]
        
        file_path = os.path.join(TEACHER_FOLDER, file_name)
       
        print("fily_type = ", file_type)
        recebePacoteGrande(serverSocket, int(qtde_pacotes), file_path, checksum)
     