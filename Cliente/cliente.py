import Cryptodome.Random.random as ri
import Cryptodome.Random as r
import threading as th
import logging as l
import hashlib as h
import numpy as np
import socket as s
import time as t
import os

MODELOS_POSSIVEIS = ["H_1","H_2"]
MODELOS_ALGORITMOS_POSSIVEIS = ["CGNE", "CGNR"]
SINAIS_MODELO_1_POSSIVEIS = ["Imagem_1_60x60", "Imagem_2_60x60", "Imagem_3_60x60"]
SINAIS_MODELO_2_POSSIVEIS = ["Imagem_1_30x30", "Imagem_2_30x30", "Imagem_3_30x30"]

class Cliente:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/cliente.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")
        self.__NOME_DO_USUARIO = r.get_random_bytes(8).hex().upper()
        self.__nome_arquivo = ''
        self.__modelo_tamanho = ''
        self.__modelo_imagem = ''
        self.__ganho_de_sinal = None

        self.__NOME_DO_SERVER = '127.0.0.1'
        self.__PORTA_DO_SERVER = 6000
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__TAM_BUFFER = 2048

        self.__conexao_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        #self.__conexao_socket.settimeout(None)
    
    
    def __del__(self):
        self.__nome_arquivo = ''
        self.__modelo_tamanho = ''
        self.__modelo_imagem = ''
        self.__modelo_algoritmo = ''
        self.__ganho_de_sinal = None
        
        self.logger.info(f"Deletando Socket:  {self.__ENDERECO_IP}")
        self.__conexao_socket.close()
        
        
    def titulo(self) -> None:
        print("--------------------------")
        print(f"CLIENTE: {self.__NOME_DO_USUARIO}")
        print("--------------------------\n")
        

    def mensagem_envio(self, mensagem:str) -> None:
        try:
            self.__conexao_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {self.__ENDERECO_IP} - Enviado: '{mensagem}'")
        except:
            self.logger.error(f"Removido do Servidor: {self.__ENDERECO_IP}")
            self.__conexao_socket.close()


    def mensagem_recebimento(self) -> str:
        try:
            mensagem = self.__conexao_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {self.__ENDERECO_IP} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Removido do Servidor: {self.__ENDERECO_IP}")
            self.__conexao_socket.close()


    def inicializar(self) -> None:
        inicializar = ''
        iniciar_conexao = False
        while inicializar == '':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            inicializar = input("Deseja conectar com o servidor [S/N] ? ").lower()
            match inicializar:
                case 's':
                    iniciar_conexao = True
                    self.logger.info("Iniciando conexão com Servidor")
                case 'sim':
                    iniciar_conexao = True
                    self.logger.info("Iniciando conexão com Servidor")
                case 'n':
                    iniciar_conexao = False
                    self.logger.info("Cancelamento de conexão com Servidor")
                case 'não':
                    iniciar_conexao = False
                    self.logger.info("Cancelamento de conexão com Servidor")
                case _:
                    print('A escolha precisa estar nas opções acima!')
                    self.logger.warning("Resposta para o cliente não foi aceita!")
                    t.sleep(2)
                    inicializar = ''
        return iniciar_conexao


    def fechar_conexao(self) -> None:
        self.mensagem_envio('OK-8-Desconectar servidor')
        resposta = self.mensagem_recebimento().split("-")
        
        if resposta[0] == "OK":
            print("Conexão com servidor finalizado")
            t.sleep(2)
            os.system('cls' if os.name == 'nt' else 'clear')
            return
        else:
            print("Erro ao fechar conexão")
            t.sleep(2)
            os.system('cls' if os.name == 'nt' else 'clear')
            return


    def descriptografar_arquivo(self, pacote:bytes, hash_inicio:int, hash_final:int) -> tuple[bytes, bytes, bytes]:
        nr_pacote = pacote[0:3]
        parte_checksum = pacote[hash_inicio:hash_final]
        data = pacote[hash_final+1 :]

        return nr_pacote, parte_checksum, data


    def aplicar_ganho_sinal(self) -> None:        
        g = np.genfromtxt("images/" + self.__nome_arquivo, delimiter='\n')
        N = 64
        S = 794 if self.__modelo_tamanho == "H_1" else 436
        self.logger.info(f"Aplicando ganho de sinal: {self.__nome_arquivo}") 

        if len(g) != N * S:
            self.logger.error(f"Tamanho de g ({len(g)}) não corresponde ao esperado ({N} x {S} = {N * S})")
            raise ValueError(f"Tamanho de g ({len(g)}) não corresponde ao esperado ({N} x {S} = {N * S})")

        for c in range(N):
            for l in range(S):
                y = 100 + (1 / 20) * l * np.sqrt(l)
                g[l + c * S] = g[l + c * S] * y  
        return g


    def aleatorizar_imagens(self) -> None:
        self.__modelo_tamanho = ri.choice(MODELOS_POSSIVEIS)
        self.__modelo_algoritmo = ri.choice(MODELOS_ALGORITMOS_POSSIVEIS)
        if self.__modelo_tamanho == "H_1":
            self.__modelo_imagem = ri.choice(SINAIS_MODELO_1_POSSIVEIS)
        else:
            self.__modelo_imagem = ri.choice(SINAIS_MODELO_2_POSSIVEIS)
        self.__nome_arquivo = self.__modelo_tamanho + '-' + self.__modelo_imagem + ".csv"
        self.mensagem_envio(f'OK-{self.__NOME_DO_USUARIO}-{self.__modelo_tamanho}-{self.__modelo_imagem}-{self.__modelo_algoritmo}')
    

    def escolher_arquivo(self) -> None:
        arquivo_encontrado = False
        conjunto_arquivos = os.listdir("./images")            
        while not arquivo_encontrado:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print('Arquivos disponíveis no servidor:')
            for arquivo in conjunto_arquivos:
                print(arquivo)

            self.__nome_arquivo = input("\nDigite o nome do arquivo que você deseja receber: ")
            
            if os.path.exists(os.path.join("./images", self.__nome_arquivo)):
                arquivo_encontrado = True
            else:
                print('A escolha precisa estar nas opções acima!')
                t.sleep(2)
        
        modelos = self.__nome_arquivo.split("-")
        self.__modelo_tamanho = modelos[0]
        self.__modelo_imagem = modelos[1].split(".")[0]
        
        self.__nome_arquivo = self.__modelo_tamanho + '-' + self.__modelo_imagem + ".csv"
        self.mensagem_envio(f'OK-{self.__NOME_DO_USUARIO}-{self.__modelo_tamanho}-{self.__modelo_imagem}')


    def enviar_modelo(self) -> None:
        resposta = self.mensagem_recebimento().split("-")
        if resposta[0] == "OK":
            self.__ganho_de_sinal = self.aplicar_ganho_sinal()
            self.logger.info("Enviando ganho de sinal") 
            ganho_sinal_byte = self.__ganho_de_sinal.tobytes()
        
            # Send the size of the serialized data first
            data_size = len(ganho_sinal_byte)
            self.__conexao_socket.sendall(data_size.to_bytes(8, byteorder='big'))
            
            # Send the serialized data in chunks
            self.__conexao_socket.sendall(ganho_sinal_byte)
            self.logger.info("Terminou o envio") 
            print("Esperando retorno..")
            retorno = self.mensagem_recebimento().split("-")
            if retorno[0] != "OK":
                self.logger.error("Retorno não concluído")
    

    def escolher_relatorio(self):
        conjunto_arquivos = []
        num_arquivos = int(self.mensagem_recebimento())
        
        if not isinstance(num_arquivos, int):
            self.mensagem_envio('ERROR-1-Má requisição')
        elif num_arquivos < 0:
            self.mensagem_envio('ERROR-2-Tamanho incongruente')
        else:
            self.mensagem_envio('OK-1-Confirmação')

        i = 0
        while i < num_arquivos:
            recv_arquivo = self.mensagem_recebimento()
            self.mensagem_envio(f"ACK-{i+1}")
            conjunto_arquivos.append(recv_arquivo)
            i+=1
            
            
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print('Arquivos disponíveis no servidor:')
            for arquivo in conjunto_arquivos:
                print(arquivo)

            nome_arquivo = input("\nDigite o nome do arquivo que você deseja receber: ")
            
            self.mensagem_envio(nome_arquivo)
            
            ok_arq = self.mensagem_recebimento().split("-")
        
            if(ok_arq[0] == 'OK'):
                break
            else:
                print('A escolha precisa estar nas opções acima!')
                t.sleep(2)
                
        return nome_arquivo


    def requisitar_relatorio(self) -> None:
        self.mensagem_envio(f'OK-{self.__NOME_DO_USUARIO}')
        nome_arquivo = self.escolher_relatorio()
        
        archive = nome_arquivo.split(".")
        nome_arquivo = archive[0] + "_cliente." + archive[1]
        dados = self.mensagem_recebimento().split("-")
        self.mensagem_envio("OK-1-Confirmação")
        
        if(dados[0] == "OK"):
            os.makedirs("./download", exist_ok=True)
            
            num_pacotes = int(dados[2])
            num_digitos = int(dados[3])
            tam_buffer = int(dados[4])
            checksum = dados[5]
            
            hash_inicio = num_digitos + 1
            hash_final = hash_inicio + 16
            checksum_completo = h.md5()
            
            with open(os.path.join("./download", nome_arquivo), "wb") as arquivo:
                for i in range(0, num_pacotes):
                    packet = self.__conexao_socket.recv(tam_buffer)

                    nr_pacote, parte_checksum, data = self.descriptografar_arquivo(packet, hash_inicio, hash_final)

                    while h.md5(data).digest() != parte_checksum:
                        try:
                            self.__conexao_socket.send(b"NOK")
                            self.logger.warning(f"Destinatário: {self.__ENDERECO_IP} - Enviado: NOK no pacote '{i+1}'")
                        except:
                            self.logger.error(f"Removido do Servidor:  {self.__ENDERECO_IP}")
                            self.__conexao_socket.close()
                        
                        packet = self.__conexao_socket.recv(tam_buffer)
                        self.logger.warning(f"Destinatário: {self.__ENDERECO_IP} - Recebido novamente: Pacote '{i+1}'")
                        
                        nr_pacote, parte_checksum, data = self.descriptografar_arquivo(packet, hash_inicio, hash_final)

                    checksum_completo.update(data)
                    arquivo.write(data)
                    self.mensagem_envio(f"ACK-{i+1}")
            
            arquivo.close()
            
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            if checksum_completo.hexdigest() == checksum:
                print("Arquivo transferido com sucesso!")
                self.logger.info(f"'OK-4-Arquivo transferido com sucesso!'")
            else:
                print("Transferência de arquivo não teve sucesso!")
                self.logger.error(f"'ERROR-4-Transferência de arquivo não teve sucesso!'")
            t.sleep(2)


    def opcoes_cliente(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print("0) Enviar 10 solitações aleatórias")
        print("1) Solicitar arquivo aleatório.")
        print("2) Solicitar arquivo específico.")
        print("3) Receber resultados.")
        print("4) Fechar conexão com o Servidor.\n")
        
        opcao = int(input("Escolha uma opção: "))
        match opcao:
            case 0:
                for _ in range(10):
                    self.mensagem_envio('OPTION-1-Solicitar arquivo aleatório')
                    self.aleatorizar_imagens()
                    self.enviar_modelo()
                    self.__ganho_de_sinal = None
                    t.sleep(r.uniform(1, 5))
            case 1:
                self.mensagem_envio('OPTION-1-Solicitar arquivo aleatório')
                self.aleatorizar_imagens()
                self.enviar_modelo()
                self.__ganho_de_sinal = None
                self.opcoes_cliente()
            case 2:
                self.mensagem_envio('OPTION-2-Solicitar arquivo específico')
                self.escolher_arquivo()
                self.enviar_modelo()
                self.__ganho_de_sinal = None
                self.opcoes_cliente()
            case 3:
                self.mensagem_envio('OPTION-3-Receber Resultados')
                self.requisitar_relatorio()
                self.__ganho_de_sinal = None
                self.opcoes_cliente()
            case 4:
                self.mensagem_envio('OPTION-4-Fechar conexão')
                self.fechar_conexao()
            case _:
                print('A escolha precisa estar nas opções acima!')
                t.sleep(2)
                self.opcoes_cliente()
                
                
    def run(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

        iniciar_conexao = self.inicializar()
        self.__conexao_socket.connect(self.__ENDERECO_IP)

        try:
            if iniciar_conexao:
                self.logger.info(f"Cliente conectado ao servidor: {self.__ENDERECO_IP}")
                self.opcoes_cliente()
        except TimeoutError:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("ERROR-5-Excedeu-se o tempo para comunicação entre o servidor e o cliente!")
        except Exception as e:
            #os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("ERROR-0-Erro não registrado!")
            print(e)


if __name__ == "__main__": 
    cliente = Cliente()
    cliente.run()