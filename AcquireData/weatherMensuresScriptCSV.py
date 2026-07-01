import csv
import os
import time
import threading
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

# Configurações
URL = "http://weather.local/measures"
CSV_FILE = "weather_data.csv"
FETCH_INTERVAL = 60  # segundos
COLUMNS = ["temperature", "humidity", "pressure", "altitude"]  # índices 1 a 4

# Controle de parada e sincronização de arquivo
stop_event = threading.Event()
file_lock = threading.Lock()

def initialize_csv():
    """Cria o arquivo CSV com cabeçalho, se não existir ou estiver vazio."""
    if not os.path.isfile(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp"] + COLUMNS)

def fetch_and_save():
    """Obtém os dados da API e os adiciona ao CSV com timestamp."""
    try:
        resp = requests.get(URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        # timestamp no formato dia:hora:min (ex: 28:14:30)
        ts = datetime.now().strftime("%d:%m:%Y %H:%M")
        row = [ts] + [data[col] for col in COLUMNS]

        with file_lock:
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        print(f"[{datetime.now().strftime('%d:%m:%Y %H:%M')}] Dados salvos: {row}")

    except Exception as e:
        print(f"Erro ao buscar ou salvar: {e}")

def background_loop():
    """Loop executado em thread separada para coletar dados a cada intervalo."""
    while not stop_event.is_set():
        fetch_and_save()
        # Espera 60 segundos, mas verifica stop_event a cada segundo
        for _ in range(FETCH_INTERVAL):
            if stop_event.is_set():
                break
            time.sleep(1)

def load_data():
    """Lê o CSV e retorna listas de timestamps e valores para cada coluna."""
    timestamps = []
    values = {col: [] for col in COLUMNS}

    with file_lock:
        with open(CSV_FILE, "r") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # pula cabeçalho
            for row in reader:
                if len(row) < 5:
                    continue
                timestamps.append(row[0])
                for i, col in enumerate(COLUMNS, start=1):
                    try:
                        values[col].append(float(row[i]))
                    except ValueError:
                        values[col].append(None)

    return timestamps, values

def plot_show(indices):
    """
    Gera gráfico com as colunas selecionadas.
    indices: lista de inteiros (1 a 4) correspondendo a:
        1=temperature, 2=humidity, 3=pressure, 4=altitude
    """
    timestamps, values = load_data()
    if not timestamps:
        print("Nenhum dado disponível para plotar.")
        return

    # Valida índices
    valid_indices = [i for i in indices if 1 <= i <= 4]
    if not valid_indices:
        print("Índices inválidos. Use números de 1 a 4 separados por vírgula.")
        return

    plt.figure(figsize=(10, 6))
    for idx in valid_indices:
        col = COLUMNS[idx - 1]
        plt.plot(timestamps, values[col], label=col, marker='o', markersize=3)

    plt.xlabel("Tempo (dia:hora:min)")
    plt.ylabel("Valor")
    plt.title("Medições da estação meteorológica")
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Mostra gráfico sem bloquear a thread principal
    plt.show(block=False)
    plt.pause(0.001)  # necessário para renderizar com block=False

def plot_show2(indices):
    """
    Gera gráfico com as colunas selecionadas.
    indices: lista de inteiros (1 a 4) correspondendo a:
        1=temperature, 2=humidity, 3=pressure, 4=altitude
    """
    timestamps, values = load_data()
    if not timestamps:
        print("Nenhum dado disponível para plotar.")
        return

    # Valida índices
    valid_indices = [i for i in indices if 1 <= i <= 4]
    if not valid_indices:
        print("Índices inválidos. Use números de 1 a 4 separados por vírgula.")
        return

    # Converte timestamps para datetime (formato esperado: "%d:%m:%Y %H:%M")
    try:
        dt_list = [datetime.strptime(ts, "%d:%m:%Y %H:%M") for ts in timestamps]
    except ValueError:
        # Fallback para formato antigo "%d:%H:%M" (caso exista)
        try:
            dt_list = [datetime.strptime(ts, "%d:%H:%M") for ts in timestamps]
        except:
            print("Formato de timestamp não reconhecido. Use 'dd:mm:yyyy HH:MM'.")
            return

    if not dt_list:
        return

    # Determina intervalo total
    t_min = dt_list[0]
    t_max = dt_list[-1]
    delta = t_max - t_min
    total_days = delta.total_seconds() / 86400

    # Escolhe formato do rótulo e descrição do eixo X
    if total_days <= 2:
        fmt = "%d/%m %H:%M"
        xlabel = "Tempo (dia/mês hora:minuto)"
    elif total_days <= 30:
        fmt = "%d/%m"
        xlabel = "Tempo (dia/mês)"
    elif total_days <= 365:
        fmt = "%m/%Y"
        xlabel = "Tempo (mês/ano)"
    else:
        fmt = "%Y"
        xlabel = "Tempo (ano)"

    # Seleciona até 10 índices igualmente espaçados
    n = len(dt_list)
    num_ticks = min(10, n)
    indices_ticks = np.linspace(0, n-1, num_ticks, dtype=int)
    tick_positions = indices_ticks
    tick_labels = [dt_list[i].strftime(fmt) for i in indices_ticks]

    # Cria o gráfico
    plt.figure(figsize=(10, 6))
    for idx in valid_indices:
        col = COLUMNS[idx - 1]
        # Converte valores para float, ignorando None
        y_vals = [v if v is not None else float('nan') for v in values[col]]
        plt.plot(timestamps, y_vals, label=col, marker='o', markersize=3)

    plt.xlabel(xlabel)
    plt.ylabel("Valor")
    plt.title("Medições da estação meteorológica")
    plt.legend()

    # Aplica os ticks personalizados
    plt.xticks(ticks=tick_positions, labels=tick_labels, rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Mostra gráfico sem bloquear
    plt.show(block=False)
    plt.pause(0.001)

# Variável global para controlar a figura atual (opcional)
_current_fig = None

def plot_show3(indices):
    """
    Gera gráfico com as colunas selecionadas.
    indices: lista de inteiros (1 a 4) correspondendo a:
        1=temperature, 2=humidity, 3=pressure, 4=altitude
    """
    global _current_fig

    timestamps, values = load_data()
    if not timestamps:
        print("Nenhum dado disponível para plotar.")
        return

    # Valida índices
    valid_indices = [i for i in indices if 1 <= i <= 4]
    if not valid_indices:
        print("Índices inválidos. Use números de 1 a 4 separados por vírgula.")
        return

    # Converte timestamps para datetime (formato esperado: "%d:%m:%Y %H:%M")
    try:
        dt_list = [datetime.strptime(ts, "%d:%m:%Y %H:%M") for ts in timestamps]
    except ValueError:
        # Fallback para formato antigo "%d:%H:%M" (caso exista)
        try:
            dt_list = [datetime.strptime(ts, "%d:%H:%M") for ts in timestamps]
        except:
            print("Formato de timestamp não reconhecido. Use 'dd:mm:yyyy HH:MM'.")
            return

    if not dt_list:
        return

    # Determina intervalo total
    t_min = dt_list[0]
    t_max = dt_list[-1]
    delta = t_max - t_min
    total_days = delta.total_seconds() / 86400

    # Escolhe formato do rótulo e descrição do eixo X
    if total_days <= 2:
        fmt = "%d/%m %H:%M"
        xlabel = "Tempo (dia/mês hora:minuto)"
    elif total_days <= 30:
        fmt = "%d/%m"
        xlabel = "Tempo (dia/mês)"
    elif total_days <= 365:
        fmt = "%m/%Y"
        xlabel = "Tempo (mês/ano)"
    else:
        fmt = "%Y"
        xlabel = "Tempo (ano)"

    # Seleciona até 10 índices igualmente espaçados
    n = len(dt_list)
    num_ticks = min(10, n)
    indices_ticks = np.linspace(0, n-1, num_ticks, dtype=int)
    tick_positions = indices_ticks
    tick_labels = [dt_list[i].strftime(fmt) for i in indices_ticks]

    # Fecha a figura anterior se existir (evita acúmulo)
    if _current_fig is not None:
        try:
            plt.close(_current_fig)
        except:
            pass
        _current_fig = None

    # Ativa o modo interativo (garante que show() não bloqueie)
    plt.ion()

    # Cria a figura
    fig = plt.figure(figsize=(10, 6))
    for idx in valid_indices:
        col = COLUMNS[idx - 1]
        y_vals = [v if v is not None else float('nan') for v in values[col]]
        plt.plot(timestamps, y_vals, label=col, marker='o', markersize=3)

    plt.xlabel(xlabel)
    plt.ylabel("Valor")
    plt.title("Medições da estação meteorológica")
    plt.legend()

    # Aplica os ticks personalizados
    plt.xticks(ticks=tick_positions, labels=tick_labels, rotation=45, ha='right')
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Mostra a figura sem bloquear (com tratamento de exceção)
    try:
        plt.show(block=False)
        # Pequena pausa para renderizar a janela
        plt.pause(0.1)
        # Guarda a referência para fechar depois
        _current_fig = fig
    except Exception as e:
        print(f"Erro ao exibir gráfico: {e}")
        # Se falhar, tenta o modo tradicional (bloqueante) em uma thread?
        # Mas aqui apenas ignoramos para não parar o script.
        pass

def process_command(cmd):
    """Interpreta e executa os comandos do usuário."""
    if cmd.lower() == "exit":
        print("Encerrando o programa...")
        stop_event.set()
        return True

    if cmd.lower().startswith("show"):
        parts = cmd.split(maxsplit=1)
        if len(parts) == 1:
            print("Uso: show 1,2,3,4  (mostra os gráficos das colunas selecionadas)")
            return False

        arg = parts[1].strip()
        try:
            indices = [int(x.strip()) for x in arg.split(",") if x.strip()]
            plot_show3(indices)
        except ValueError:
            print("Formato inválido. Use números separados por vírgula, ex: show 1,3,4")
        return False

    print("Comando desconhecido. Comandos disponíveis: exit, show <lista>")
    return False

def main():
    initialize_csv()

    # Inicia thread de coleta
    collector = threading.Thread(target=background_loop, daemon=True)
    collector.start()

    print("Sistema de monitoramento iniciado.")
    print("Comandos: exit | show 1,2,3,4 (ex: show 3,4 para pressão e altitude)")
    print("Pressione Enter para continuar ou digite um comando.\n")

    # Loop principal de entrada do usuário
    try:
        while not stop_event.is_set():
            try:
                cmd = input("> ").strip()
                if cmd:
                    should_exit = process_command(cmd)
                    if should_exit:
                        break
            except EOFError:
                break
            except KeyboardInterrupt:
                break
    finally:
        # Encerra a thread de coleta
        stop_event.set()
        collector.join(timeout=2)
        print("Programa finalizado.")

if __name__ == "__main__":
    main()