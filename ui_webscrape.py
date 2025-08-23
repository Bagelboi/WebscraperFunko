import subprocess
import sys
from InquirerPy import inquirer

def main():
    while True:
        escolha = inquirer.select(
            message="Escolha uma opção:",
            choices=[
                "Criar excel com ofertas",
                "Mostrar imagens",
                "Sair",
            ],
        ).execute()

        if escolha == "Criar excel com ofertas":
            directory = input("Digite o diretorio das imagens: ")
            json_directory = input("Digite o diretorio dos json: ")
            excel_file = input("Digite o nome do arquivo excel: ") + ".xlsx"
            chunk_size = input("Digite a quantidade de ofertas processadas simultaneamente:  ")

            subprocess.run(
                [sys.executable, "webscrape.py", directory, json_directory, excel_file, chunk_size]
            )

        elif escolha == "Mostrar imagens":
            directory = input("Digite o diretorio dos json: ")
            item_max = input("Digite o maximo de imagens por item: ")
            output_folder = input("Digite o diretorio de saida para as imagens: ")
            ordered = input("Digite a quantidade de imagens para serem ordenadas por relevancia: ")

            subprocess.run(
                [sys.executable, "webscrape_image.py", directory, item_max, output_folder, ordered]
            )

        elif escolha == "Sair":
            print("Saindo...")
            break

if __name__ == "__main__":
    main()
