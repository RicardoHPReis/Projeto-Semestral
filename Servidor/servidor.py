import matplotlib.pyplot as plt
import threading as th
import logging as l
import hashlib as h
import numpy as np
import socket as s
import time as t
import datetime as d
import psutil as ps
import csv
import os
import queue

class Servidor:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servidor.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 6000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        
        self.__clientes = []
        
        self.__H_1 = None
        self.__H_2 = None
        MAX_CLIENTES_SIMULTANEOS = 3

        # Crie um semáforo para controlar o número de clientes que podem processar
        self.semaphore = th.Semaphore(MAX_CLIENTES_SIMULTANEOS)

        # Crie uma fila para armazenar os clientes que estão esperando
        self.fila_espera = queue.Queue()
    
        self.__server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__server_socket.bind(self.__ENDERECO_IP)
        self.__server_socket.listen()
        self.logger.info(f"Socket do servidor criado na porta: '{self.__PORTA_DO_SERVER}'")
        
    
    def __del__(self):
        self.__H_1 = None
        self.__H_2 = None
        
        self.logger.info(f"Socket finalizado!")
        for cliente in self.__clientes:
            self.cliente.close()
            
        self.__clientes.clear()
        self.__server_socket.close()
        #os.system('cls' if os.name == 'nt' else 'clear')
        
    
    def titulo(self) -> None:
        print("--------------------")
        print("      SERVIDOR")
        print("--------------------\n")


    def mensagem_envio(self, cliente_socket:s.socket, endereco:tuple, mensagem:str) -> None:
        try:
            cliente_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {endereco} - Enviado:  '{mensagem}'")
        except:
            self.logger.error(f"Cliente removido: {endereco}")
            self.__clientes.remove(cliente_socket)


    def mensagem_recebimento(self, cliente_socket:s.socket, endereco:tuple) -> str:
        try:
            mensagem = cliente_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {endereco} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Cliente removido: {endereco}")
            self.__clientes.remove(cliente_socket)
        

    def iniciar_servidor(self) -> None:
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


    def processar_cliente(self, cliente_socket:s.socket, endereco:tuple, modelo:str, modelo_imagem:str, nome_usuario:str, modelo_algoritmo:str) -> None:
        try:
            self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
            ganho_de_sinal = self.receber_ganho_sinal(cliente_socket, endereco)
            self.reconstruir_imagem(cliente_socket, endereco, modelo, modelo_imagem, ganho_de_sinal, nome_usuario, modelo_algoritmo)
            ganho_de_sinal = None
        finally:
            self.semaphore.release()
            if not self.fila_espera.empty():
                proximo_cliente = self.fila_espera.get()
                proximo_cliente.start()


    def opcoes_servidor(self, cliente_socket:s.socket, endereco:tuple) -> None:
        #os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        opcao = 0
        cliente_opcao = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        
        if cliente_opcao[0] == 'OPTION':
            opcao = int(cliente_opcao[1])
            
        match opcao:
            case 1:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                modelo = resposta[2]
                modelo_imagem = resposta[3]
                nome_usuario = resposta[1]
                modelo_algoritmo = resposta[4]
                if resposta[0] == "OK":
                    if not self.semaphore.acquire(blocking=False):  # Tenta adquirir o semáforo sem bloquear
                        self.fila_espera.put(th.Thread(target=self.processar_cliente, args=(cliente_socket, endereco, modelo, modelo_imagem, nome_usuario, modelo_algoritmo)))
                        #self.mensagem_envio(cliente_socket, endereco, 'WAIT-Espere na fila')
                        return
                    try:
                        self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
                        ganho_de_sinal = self.receber_ganho_sinal(cliente_socket, endereco)
                        self.reconstruir_imagem(cliente_socket, endereco, modelo, modelo_imagem, ganho_de_sinal, nome_usuario, modelo_algoritmo)
                        ganho_de_sinal = None
                    finally:
                        self.semaphore.release()
                        if not self.fila_espera.empty():
                            proximo_cliente = self.fila_espera.get()
                            proximo_cliente.start()
            case 2:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                modelo = resposta[2]
                modelo_imagem = resposta[3]
                nome_usuario = resposta[1]
                modelo_algoritmo = resposta[4]
                if resposta[0] == "OK":
                    self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
                    ganho_de_sinal = self.receber_ganho_sinal(cliente_socket, endereco)
                    self.reconstruir_imagem(cliente_socket, endereco, modelo, modelo_imagem, ganho_de_sinal, nome_usuario, modelo_algoritmo)
                    ganho_de_sinal = None
                    self.opcoes_servidor(cliente_socket, endereco)
            case 3:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                modelo = resposta[2]
                modelo_imagem = resposta[3]
                nome_usuario = resposta[1]
                modelo_algoritmo = resposta[4]
                if resposta[0] == "OK":
                    self.mensagem_envio(cliente_socket, endereco, 'OK-Pode receber')
                    ganho_de_sinal = self.receber_ganho_sinal(cliente_socket, endereco)
                    self.reconstruir_imagem(cliente_socket, endereco, modelo, modelo_imagem, ganho_de_sinal, nome_usuario, modelo_algoritmo)
                    self.opcoes_servidor(cliente_socket, endereco)
            case 4:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                nome_usuario = resposta[1]
                self.enviar_relatorio(cliente_socket, endereco, nome_usuario)
                self.opcoes_servidor(cliente_socket, endereco)
            case 5:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                if resposta[0] == "OK":
                    self.logger.warning(f"Cliente desconectado: {endereco}")
                    self.__clientes.remove(cliente_socket)
                    self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
                    
                    #os.system('cls' if os.name == 'nt' else 'clear')
                    self.titulo()
                    print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


    def checksum_arquivo(self, nome_arquivo: str) -> str:
        checksum = h.md5()
        with open(os.path.join("./content", nome_arquivo), "rb") as file:
            while data := file.read(self.__TAM_BUFFER):
                checksum.update(data)

        return checksum.hexdigest()
        

    def enviar_relatorio(self, cliente_socket:s.socket, endereco:tuple, nome_usuario:str) -> None:
        nome_arquivo: str = self.retornar_nome_arquivos(cliente_socket, endereco, nome_usuario)
        if nome_arquivo == "":
            return
        
        num_pacotes: int = (os.path.getsize(os.path.join("./content", nome_arquivo)) // self.__TAM_BUFFER) + 1
        num_digitos: int = len(str(num_pacotes))
        num_buffer: int = num_digitos + 1 + 16 + 1 + self.__TAM_BUFFER
        checksum: str = self.checksum_arquivo(nome_arquivo)

        self.mensagem_envio(cliente_socket, endereco, f"OK-2-{num_pacotes}-{num_digitos}-{num_buffer}-{checksum}")
        inicio = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        if inicio[0] != "OK":
            return

        with open(os.path.join("./content", nome_arquivo), "rb") as arquivo:
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


    def retornar_nome_arquivos(self, cliente_socket:s.socket, endereco:tuple, nome_usuario:str) -> str:
        #os.system('cls' if os.name == 'nt' else 'clear')

        file_paths = os.listdir("./content")
        arquivos_usuario = []
        for arq in file_paths:
            if nome_usuario in arq:
                arquivos_usuario.append(arq)
                
        num_arquivos = len(arquivos_usuario)

        self.mensagem_envio(cliente_socket, endereco, str(num_arquivos))
        
        confirmacao_tam = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        
        if(confirmacao_tam[0] == "ERROR"):
            self.logger.error("ERRO-1-Erro na requisição")
            #os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("Erro na Requisição")
            t.sleep(2)
            #os.system('cls' if os.name == 'nt' else 'clear')
            return ""
        
        elif(num_arquivos <= 0):
            self.logger.error("ERRO-2-Nenhum arquivo no servidor")
            #os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("Nenhum arquivo no servidor")
            t.sleep(2)
            #os.system('cls' if os.name == 'nt' else 'clear')
            return ""
            
        else:
            i = 0
            while i < num_arquivos:
                self.mensagem_envio(cliente_socket, endereco, arquivos_usuario[i])
                ack = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                if (ack[1] == str(i+1)):
                    i += 1
                
            while True:
                nome_arquivo = self.mensagem_recebimento(cliente_socket, endereco)
                    
                if nome_arquivo not in arquivos_usuario:
                    self.mensagem_envio(cliente_socket, endereco, "ERROR-3-Arquivo não encontrado!")
                else:
                    self.mensagem_envio(cliente_socket, endereco, 'OK-1-Confirmação')
                    break
            return nome_arquivo


    def calcular_CGNE(self, g:np.ndarray, modelo:str) -> tuple[np.ndarray, int]:
        # Inicializa f como um vetor de zeros
        f = np.zeros(self.__H_1.shape[1]) if modelo == "H_1" else np.zeros(self.__H_2.shape[1])
        r = g - np.dot(self.__H_1, f) if modelo == "H_1" else g - np.dot(self.__H_2, f)
        p = np.dot(self.__H_1.T, r) if modelo == "H_1" else np.dot(self.__H_2.T, r)
        iter_count = 0

        porc = len(g)//100
        antigo = -1
        for i in range(len(g)):
            alpha = np.dot(r.T, r) / np.dot(p.T, p)
            f = f + alpha * p
            r_next = r - alpha * np.dot(self.__H_1, p) if modelo == "H_1" else r - alpha * np.dot(self.__H_2, p)

            error = abs(np.linalg.norm(r, ord = 2) - np.linalg.norm(r_next, ord = 2))
            if error < 1e-4:
                self.logger.info("Erro menor que 1e-4")
                break

            if iter_count > 10:
                self.logger.info("Passou de 10 interações")
                break

            beta = np.dot(r_next.T, r_next) / np.dot(r.T, r)
            p = beta * p + np.dot(self.__H_1.T, r_next) if modelo == "H_1" else beta * p + np.dot(self.__H_2.T, r_next)
            r = r_next
                
            iter_count += 1            
            if antigo < i//porc:
                antigo+=1
                #os.system('cls' if os.name == 'nt' else 'clear')
                self.titulo()
                print(f'Processamento: {antigo}% de {len(g)} pacotes')
                self.logger.info(f'Processamento: {antigo}% de {len(g)} pacotes')

        print('Terminou o processamento')
        self.logger.info(f"Terminou o processamento")
        return f, iter_count
    
    
    def calcular_CGNR(self, g:np.ndarray, modelo:str) -> tuple[np.ndarray, int]:
        # Inicializa f como um vetor de zeros
        f = np.zeros(self.__H_1.shape[1]) if modelo == "H_1" else np.zeros(self.__H_2.shape[1])
        r = g - np.dot(self.__H_1, f) if modelo == "H_1" else g - np.dot(self.__H_2, f)
        z = np.dot(self.__H_1.T, r) if modelo == "H_1" else np.dot(self.__H_2.T, r)
        p = z
        iter_count = 0

        porc = len(g)//100
        antigo = -1
        for i in range(len(g)):
            w = np.dot(self.__H_1, p) if modelo == "H_1" else np.dot(self.__H_2, p)
            alpha = np.dot(z.T, z) / np.dot(w.T, w)
            f = f + alpha * p
            r_next = r - alpha * w
            z_next = np.dot(self.__H_1.T, r_next) if modelo == "H_1" else np.dot(self.__H_2.T, r_next)

            error = abs(np.linalg.norm(r, ord = 2) - np.linalg.norm(r_next, ord = 2))
            if error < 1e-4:
                self.logger.info("Erro menor que 1e-4")
                break

            beta = np.dot(z_next.T, z_next) / np.dot(z.T, z)
            p = z_next + beta * p
            r = r_next
            z = z_next
                
            iter_count += 1            
            if antigo < i//porc:
                antigo+=1
                #os.system('cls' if os.name == 'nt' else 'clear')
                self.titulo()
                print(f'Processamento: {antigo}% de {len(g)} pacotes')
                self.logger.info(f'Processamento: {antigo}% de {len(g)} pacotes')

        print('Terminou o processamento')
        self.logger.info(f"Terminou o processamento")
        return f, iter_count
    
    
    def receber_ganho_sinal(self, cliente_socket:s.socket, endereco:tuple) -> None:
        data_size = cliente_socket.recv(8)
        size = int.from_bytes(data_size, byteorder='big') 
        self.logger.info(f"Remetente: {endereco} - Recebido: 'Tamanho dos dados {size}'")
        
        i=0
        received_data = bytearray()
        while len(received_data) < size:
            chunk = cliente_socket.recv(4096)
            self.logger.info(f"Remetente: {endereco} - Recebido: 'ACK-{i+1}'")
            if not chunk:
                break
            received_data.extend(chunk)
            i+=1
        
        self.logger.info(f"'OK-4-Todos os {i} pacotes foram enviados!'")
        return np.frombuffer(received_data, dtype=np.float64)

    
    def reconstruir_imagem(self, cliente_socket:s.socket, endereco:tuple, modelo:str, modelo_imagem:str, ganho_de_sinal:np.ndarray, nome_usuario:str, modelo_algoritmo:str) -> None:
        process = ps.Process(os.getpid())
        
        horario_inicio = d.datetime.now()
        start_time = t.time()
        start_cpu = process.cpu_percent(interval=None)
        start_mem = process.memory_info().rss
        
        nome_arquivo = nome_usuario + "-" + modelo + "-" + modelo_imagem + "-" + modelo_algoritmo
        
        resultado = None
        iter_count = 0
        if modelo_algoritmo == "CGNE":
            resultado, iter_count = self.calcular_CGNE(ganho_de_sinal, modelo)
        else:
            resultado, iter_count = self.calcular_CGNR(ganho_de_sinal, modelo)
            
        len_image  = int(np.sqrt(len(resultado)))
        resultado = resultado.reshape((len_image, len_image), order='F')
        
        horario_fim = d.datetime.now()
        end_time = t.time()
        end_cpu = process.cpu_percent(interval=None)
        end_mem = process.memory_info().rss
    
        total_time = end_time - start_time        
        cpu_usage = end_cpu - start_cpu
        memory_usage = (end_mem - start_mem) / (1024 ** 2)  
        
        informacoes = (
            f"Usuário: {nome_usuario}\n"
            f"Iterações: {iter_count}\n"
            f"Tempo Inicial: {horario_inicio.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Tempo Final: {horario_fim.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Tempo Total (s): {total_time:.2f}\n"
            f"Uso de CPU (%): {cpu_usage:.2f}\n"
            f"Uso de Memória (MB): {memory_usage:.2f}"
        )
        
        #relatorio 
        plt.imshow(resultado, 'gray')
        plt.title('Relatório de Desempenho')
        plt.gcf().text(0.02, 0.5, informacoes, fontsize=10, color='white', ha='left', va='center', bbox=dict(facecolor='black', alpha=0.5))
        print(iter_count)
        plt.savefig(f'content/{nome_arquivo}.png')
        plt.close()
        
        self.logger.info(f"Relatório de desempenho salvo em content/{nome_arquivo}.png")
        self.mensagem_envio(cliente_socket, endereco, 'OK-Processo terminado')


    def run(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Lendo arquivos base...')
        if not os.path.exists("./data/H_1.npy") or not os.path.exists("./data/H_2.npy"):
            # Se não existirem, lê os CSVs e salva como .npy
            self.__H_1 = np.genfromtxt("./data/H_1.csv", delimiter=',')
            self.__H_2 = np.genfromtxt("./data/H_2.csv", delimiter=',')
            np.save("./data/H_1.npy", self.__H_1)
            np.save("./data/H_2.npy", self.__H_2)
        else:
            # Se existirem, carrega diretamente os .npy
            self.__H_1 = np.load("./data/H_1.npy")
            self.__H_2 = np.load("./data/H_2.npy")

        
        os.system('cls' if os.name == 'nt' else 'clear')
        iniciar_server = self.iniciar_servidor()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta...')

        while iniciar_server:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            thread = th.Thread(target=self.opcoes_servidor, args=(cliente_socket, endereco), daemon=True)
            thread.start()


if __name__ == "__main__":
    server = Servidor()
    server.run()