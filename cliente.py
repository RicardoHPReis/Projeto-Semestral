import socket as s
import time as t
import logging as l
import hashlib as h
import threading as th
import numpy as n
import pyblas.level1 as blas
import scipy as sp
import scipy.linalg as la
import os


class Cliente:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/cliente.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")
        
        self.__NOME_DO_SERVER = '127.0.0.1'
        self.__PORTA_DO_SERVER = 6000
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__TAM_BUFFER = 2048

        self.__conexao_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__conexao_socket.settimeout(30)
    
    
    def __del__(self):
        self.logger.info(f"Deletando Socket:  {self.__ENDERECO_IP}")
        self.__conexao_socket.close()
        
        
    def titulo(self):
        print("--------------------")
        print("       CLIENTE")
        print("--------------------\n")
        

    def mensagem_envio(self, mensagem : str):
        try:
            self.__conexao_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {self.__ENDERECO_IP} - Enviado: '{mensagem}'")
        except:
            self.logger.error(f"Removido do Servidor: {self.__ENDERECO_IP}")
            self.__conexao_socket.close()


    def mensagem_recebimento(self):
        try:
            mensagem = self.__conexao_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {self.__ENDERECO_IP} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Removido do Servidor: {self.__ENDERECO_IP}")
            self.__conexao_socket.close()


    def inicializar(self):
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


    def fechar_conexao(self):
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
                

    def escolher_arquivo(self):
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


    def descriptografar_arquivo(self, pacote : bytes, hash_inicio : int, hash_final : int) -> tuple[bytes, bytes, bytes]:
        nr_pacote = pacote[0:3]
        parte_checksum = pacote[hash_inicio:hash_final]
        data = pacote[hash_final+1 :]

        return nr_pacote, parte_checksum, data


    def requisitar_arquivo(self):
        nome_arquivo = self.escolher_arquivo()
        
        archive = nome_arquivo.split(".")
        nome_arquivo = archive[0] + "_cliente." + archive[1]
        dados = self.mensagem_recebimento().split("-")
        self.mensagem_envio("OK-1-Confirmação")
        
        if(dados[0] == "OK"):
            os.makedirs("./Recebidos", exist_ok=True)
            
            num_pacotes = int(dados[2])
            num_digitos = int(dados[3])
            tam_buffer = int(dados[4])
            checksum = dados[5]
            
            hash_inicio = num_digitos + 1
            hash_final = hash_inicio + 16
            checksum_completo = h.md5()
            
            with open(os.path.join("./Recebidos", nome_arquivo), "wb") as arquivo:
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
            

    def opcoes_cliente(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('1) Solicitar arquivo.')
        print('2) Fechar conexão com o Servidor.\n')
        
        opcao = int(input("Escolha uma opção: "))
        match opcao:
            case 1:
                self.mensagem_envio('OPTION-1-Requisição de arquivo')
                self.requisitar_arquivo()
                self.opcoes_cliente()
            case 2:
                self.mensagem_envio('OPTION-2-Desconectando do Servidor')
                self.fechar_conexao()
            case _:
                print('A escolha precisa estar nas opções acima!')
                t.sleep(2)
                self.opcoes_cliente()
                
                
    def run(self):
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
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print("ERROR-0-Erro não registrado!")
            print(e)


if __name__ == "__main__": 
    cliente = Cliente()
    cliente.run()