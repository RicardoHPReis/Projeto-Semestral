import socket as s
import time as t
import logging as l
import hashlib as h
import threading as th
import numpy as np
import csv
import os
import matplotlib.pyplot as plt

class Servidor:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servidor.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 6000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__nome_arquivo = ""
        self.__modelo = ""
        self.__modelo_imagem = ""
        self.__ganho_de_sinal = ""
        
        self.__clientes = []

        self.__server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__server_socket.bind(self.__ENDERECO_IP)
        self.__server_socket.listen()
        self.__server_socket.settimeout(60)
        self.logger.info(f"Socket do servidor criado na porta: '{self.__PORTA_DO_SERVER}'")
        
    
    def __del__(self):
        self.logger.info(f"Socket finalizado!")
        for cliente in self.__clientes:
            self.cliente.close()
            
        self.__clientes.clear()
        self.__server_socket.close()
        #os.system('cls' if os.name == 'nt' else 'clear')
        
    
    def titulo(self):
        print("--------------------")
        print("      SERVIDOR")
        print("--------------------\n")


    def mensagem_envio(self, cliente_socket : s.socket, endereco : tuple, mensagem : str):
        try:
            cliente_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {endereco} - Enviado:  '{mensagem}'")
        except:
            self.logger.error(f"Cliente removido: {endereco}")
            self.__clientes.remove(cliente_socket)


    def mensagem_recebimento(self, cliente_socket : s.socket, endereco : tuple):
        try:
            mensagem = cliente_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {endereco} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Cliente removido: {endereco}")
            self.__clientes.remove(cliente_socket)
        

    def iniciar_servidor(self):
        inicializar = ''
        iniciar_server = False
        while inicializar == '':
            #os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            inicializar = input("Deseja inicializar o servidor [S/N] ? ").lower().strip()
            match inicializar:
                case 's':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'sim':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'n':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case 'não':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case _:
                    print('A escolha precisa estar nas opções acima!')
                    self.logger.warning("Resposta para o servidor não foi aceita!")
                    t.sleep(2)
                    inicializar = ''
        return iniciar_server


    def opcoes_servidor(self, cliente_socket:s.socket, endereco:tuple):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        opcao = 0
        cliente_opcao = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        
        if cliente_opcao[0] == 'OPTION':
            opcao = int(cliente_opcao[1])
            
        match opcao:
            case 1:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                self.__modelo = resposta[2]
                self.__modelo_imagem = resposta[3]
                if resposta[0] == "OK":
                    self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
                    self.receber_ganho_sinal(cliente_socket, endereco)
                    self.reconstruir_imagem(cliente_socket, endereco)
                    self.opcoes_servidor(cliente_socket, endereco)
            case 2:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                self.__modelo = resposta[2]
                self.__modelo_imagem = resposta[3]
                if resposta[0] == "OK":
                    self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
                    self.receber_ganho_sinal(cliente_socket, endereco)
                    self.reconstruir_imagem(cliente_socket, endereco)
                    self.opcoes_servidor(cliente_socket, endereco)
            case 3:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                if resposta[0] == "OK":
                    self.logger.warning(f"Cliente desconectado: {endereco}")
                    self.__clientes.remove(cliente_socket)
                    self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.titulo()
                    print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


    def receber_ganho_sinal(self, cliente_socket: s.socket, endereco: tuple):
        data_size = cliente_socket.recv(8)
        self.logger.info(f"Remetente: {endereco} - Recebido: 'Tamanho dos dados {data_size}'")
        size = int.from_bytes(data_size, byteorder='big') 
        
        # Receive the data in chunks
        i=0
        received_data = bytearray()
        while len(received_data) < size:
            chunk = cliente_socket.recv(4096)
            self.logger.info(f"Remetente: {endereco} - Recebido: 'ACK-{i+1}'")
            if not chunk:
                break
            received_data.extend(chunk)
            i+=1
        
        # Convert the received bytes back to a NumPy array
        self.logger.info(f"'OK-4-Todos os {i} pacotes foram enviados!'")
        self.__ganho_de_sinal = np.frombuffer(received_data, dtype=np.float64)


    def checksum_arquivo(self, nome_arquivo: str) -> str:
        checksum = h.md5()
        with open(os.path.join("./images", nome_arquivo), "rb") as file:
            while data := file.read(self.__TAM_BUFFER):
                checksum.update(data)

        return checksum.hexdigest()
    
    
    def dot_matriz(matriz_1:np.ndarray, matriz_2:np.ndarray) -> np.ndarray:
        tam_1 = matriz_1.shape
        tam_2 = matriz_2.shape
        
        if matriz_1.ndim < 2:
            tam_1 = (0, tam_1[0])
        if matriz_2.ndim < 2:
            tam_2 = (0, tam_2[0])
        
        if tam_1[1] != tam_2[0]:
            raise ValueError
        else:
            return matriz_1 @ matriz_2
    
    
    def calcular_CGNE():
        g = []
        matriz = np.array([])
        matriz_trans = []
        f0 = 0
        r0 = g - matriz*f0
        p0 = matriz_trans * r0
        for i in range(0,1000):
            matriz
    
    
    def calcular_CGNR(self, H:np.ndarray, g:np.ndarray):
        f = np.zeros(H.shape[1])  # Inicializa f como um vetor de zeros
        r = g - np.dot(H, f)
        z = np.dot(H.T, r)
        p = z
        iter_count = 0

        porc = len(g)//100
        antigo = -1
        for i in range(len(g)):
            w = np.dot(H, p)
            alpha = np.dot(z.T, z) / np.dot(w.T, w)
            f = f + alpha * p
            r_next = r - alpha * w
            z_next = np.dot(H.T, r_next)

            error = abs(np.linalg.norm(r, ord = 2) - np.linalg.norm(r_next, ord = 2))
            if error < 1e-4:
                print('Terminou o processamento')
                self.logger.info(f"Terminou o processamento")
                t.sleep(2)
                break

            beta = np.dot(z_next.T, z_next) / np.dot(z.T, z)
            p = z_next + beta * p
            r = r_next
            z = z_next
            
            iter_count += 1            
            if antigo < i//porc:
                antigo+=1
                os.system('cls' if os.name == 'nt' else 'clear')
                self.titulo()
                print(f'Processamento: {antigo}% de {len(g)} pacotes')
                self.logger.info(f'Processamento: {antigo}% de {len(g)} pacotes')

        return f, iter_count
    
    
    def reconstruir_imagem(self, cliente_socket: s.socket, endereco: tuple):    
        self.__nome_arquivo = self.__modelo + "-" + self.__modelo_imagem
        H = np.genfromtxt("data/" + self.__modelo + ".csv", delimiter=',')
        
        res_image, iter_count = self.calcular_CGNR(H, self.__ganho_de_sinal)
        len_image  = int(np.sqrt(len(res_image)))
        res_image = res_image.reshape((len_image, len_image), order='F')
        
        #plt.imshow(res_image, 'gray')
        plt.title('Log')
        print(iter_count)
        plt.savefig(f'download/{self.__nome_arquivo}.png')
        plt.close()
        
        #return res_image, iter_count

   
    def enviar_arquivo(self, cliente_socket:s.socket, endereco:tuple):
        nome_arquivo: str = self.retornar_nome_arquivos(cliente_socket, endereco)
        num_pacotes: int = (os.path.getsize(os.path.join("./images", nome_arquivo)) // self.__TAM_BUFFER) + 1
        num_digitos: int = len(str(num_pacotes))
        num_buffer: int = num_digitos + 1 + 16 + 1 + self.__TAM_BUFFER
        checksum: str = self.checksum_arquivo(nome_arquivo)
        
        #matriz = np.matrix()
        with open(os.path.join("./images", nome_arquivo), 'r') as file:
            csvFile = csv.reader(file)
            for lines in csvFile:
                print(lines)

        self.mensagem_envio(cliente_socket, endereco, f"OK-2-{num_pacotes}-{num_digitos}-{num_buffer}-{checksum}")
        inicio = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        if inicio[0] != "OK":
            return

        with open(os.path.join("./images", nome_arquivo), "rb") as arquivo:
            i = 0
            while data := arquivo.read(self.__TAM_BUFFER):
                hash_ = h.md5(data).digest()
                data_criptografada = b" ".join([f"{i:{'0'}{num_digitos}}".encode(), hash_, data])
                
                try:
                    cliente_socket.send(data_criptografada)
                    self.logger.info(f"Destinatário: {endereco} - Enviado:  'Pacote {i+1}'")
                except:
                    self.logger.error(f"Cliente removido:  {endereco}")
                    self.__clientes.remove(cliente_socket)
                    break
                
                while self.mensagem_recebimento(cliente_socket, endereco) == "NOK":
                    try:
                        cliente_socket.send(data_criptografada)
                        self.logger.warning(f"Destinatário: {endereco} - Enviado novamente:  'Pacote {i+1}'")
                    except:
                        self.logger.error(f"Cliente removido:  {endereco}")
                        self.__clientes.remove(cliente_socket)
                        break
                i += 1
        self.logger.info(f"'OK-4-Todos os {num_pacotes} foram enviados!'")


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        iniciar_server = self.iniciar_servidor()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while iniciar_server:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            
            thread = th.Thread(target=self.opcoes_servidor, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    server = Servidor()
    server.run()