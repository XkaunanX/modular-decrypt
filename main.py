import sys
import argparse
import json
from collections import OrderedDict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

sys.stdout.reconfigure(encoding='utf-8')

class DecryptSystem:
    def __init__(self, config=None):
        self.reset()
        if config:
            self.cargar_configuracion(config)

    def reset(self):
        self.tabla = {'valor': OrderedDict(), 'simbolo': {}}
        self.modulo = 0
        self.b = 0
        self.datos_descubiertos = {}
        self.mensaje_encriptado = ""
        self.semilla = None
        self.inverso = None

    def cargar_configuracion(self, config: dict):
        self.reset()
        # Construir tabla numerica
        tabla_numerica = {int(k): v for k, v in config.get('tabla', {}).items()}
        # Ordenar y asignar valor->simbolo y simbolo->valor
        self.tabla['valor'] = OrderedDict(sorted(tabla_numerica.items()))
        self.tabla['simbolo'] = {v: k for k, v in self.tabla['valor'].items()}

        # Calcular modulo automaticamente
        self.modulo = len(self.tabla['valor'])
        # Cargar b y reducir modulo
        raw_b = int(config.get('b', 0))
        self.b = raw_b % self.modulo

        # Cargar datos descubiertos y mensaje encriptado
        self.datos_descubiertos = config.get('datos_descubiertos', {})
        self.mensaje_encriptado = config.get('mensaje_encriptado', '')

    def _inverso_multiplicativo(self, valor):
        for i in range(1, self.modulo):
            if (valor * i) % self.modulo == 1:
                return i
        raise ValueError(f"No existe inverso para {valor} modulo {self.modulo}")

    def _calcular_semilla(self, console):
        # Requiere al menos dos pares de datos
        if len(self.datos_descubiertos) < 2:
            return None
        pares = []
        for orig, enc in self.datos_descubiertos.items():
            if orig in self.tabla['simbolo'] and enc in self.tabla['simbolo']:
                X = self.tabla['simbolo'][orig]
                Y = self.tabla['simbolo'][enc]
                pares.append((X, Y))

        console.log("Iniciando busqueda de semilla...")
        with Progress(
            SpinnerColumn(),
            TextColumn("Probando semilla {task.completed}/{task.total}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("busqueda", total=self.modulo - 1)
            for a in range(1, self.modulo):
                if all((a * X + self.b) % self.modulo == Y for X, Y in pares):
                    return a
                progress.advance(task)
        return None

    def procesar(self):
        console = Console()
        console.rule("[bold green]Desencriptador Modular Iniciado[/]")
        console.print(f"Modulo: [yellow]{self.modulo}[/]  |  b reducido: [yellow]{self.b}[/]\n")

        # Calcular semilla
        self.semilla = self._calcular_semilla(console)
        if self.semilla is None:
            console.print("[red]Error:[/] no se pudo calcular semilla (asegure al menos dos datos descubiertos validos)")
            return None
        console.print(f"Semilla encontrada: [bold cyan]{self.semilla}[/]")

        # Calcular inverso
        self.inverso = self._inverso_multiplicativo(self.semilla)
        console.print(f"Inverso multiplicativo: [bold cyan]{self.inverso}[/]\n")

        # Desencriptar mensaje
        console.log("Desencriptando mensaje...")
        resultado = []
        for c in self.mensaje_encriptado:
            if c in self.tabla['simbolo']:
                Y = self.tabla['simbolo'][c]
                X = ((Y - self.b) * self.inverso) % self.modulo
                resultado.append(self.tabla['valor'].get(X, '?'))
            else:
                resultado.append(c)
        mensaje = ''.join(resultado)

        table = Table(title="Resultado Desencriptacion")
        table.add_column("Mensaje Encriptado", style="magenta")
        table.add_column("Mensaje Desencriptado", style="green")
        table.add_row(self.mensaje_encriptado, mensaje)
        console.print(table)

        console.rule("[bold green]Proceso Finalizado[/]")
        return mensaje


def main():
    parser = argparse.ArgumentParser(description='Desencriptador modular con consola animada')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path al JSON de configuracion: tabla, b, datos_descubiertos, mensaje_encriptado')
    args = parser.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        config = json.load(f)

    ds = DecryptSystem(config)
    ds.procesar()

if __name__ == "__main__":
    main()
