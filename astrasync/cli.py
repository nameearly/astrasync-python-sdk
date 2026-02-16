import click
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import AstraSync, __version__
from .exceptions import AstraSyncError

console = Console()

@click.group()
@click.version_option(version=__version__)
def cli():
    """AstraSync AI - Universal AI Agent Registration"""
    pass

@cli.command()
@click.argument('agent_file', type=click.Path(exists=True))
@click.option('--email', '-e', help='Developer email')
@click.option('--output', '-o', help='Output file for credentials')
def register(agent_file, email, output):
    """Register an AI agent from any format"""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading agent file...", total=None)
            
            # FIXME(逻辑): core.AstraSync.__init__ 当前强制要求 api_key/password。
            # CLI 这里只传 email 会直接抛 ValueError，导致命令无法工作。
            # 建议：为 CLI 增加 --api-key/--password 参数并传入；或调整 SDK 的鉴权要求。
            client = AstraSync(email=email)
            
            progress.update(task, description="Registering with AstraSync...")
            # FIXME(逻辑): 这里传入的是 agent_file 路径字符串，不是解析后的 dict。
            # normalize_agent_data() 会把字符串当成 unknown，生成 Unnamed/Unknown 默认值。
            # 建议：先读取并解析文件内容（JSON/YAML 等）再传入 client.register()。
            result = client.register(agent_file)
            
            progress.update(task, description="Registration complete!")
        
        table = Table(title="✅ Registration Successful")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Agent ID", result['agentId'])
        table.add_row("Status", result['status'])
        table.add_row("Trust Score", result.get('trustScore', 'N/A'))
        
        console.print(table)
        
        if output:
            output_path = Path(output)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"\n💾 Credentials saved to {output_path}")
            
    except AstraSyncError as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)

@cli.command()
def health():
    """Check AstraSync API health"""
    # FIXME(逻辑): AstraSync() 当前构造需要 api_key/password，这里不传会直接抛 ValueError。
    # 同时 core.AstraSync 并没有 api_client/api_url 这两个属性，下面会 AttributeError。
    # 建议：实现真正的 api_client + health_check()；或 CLI 直接调用一个 utils/api.py 的 health_check()。
    client = AstraSync()
    try:
        with console.status("Checking API health..."):
            response = client.api_client.health_check()
        console.print("[green]✅ API is healthy![/green]")
        console.print(f"Endpoint: {client.api_url}")
    except Exception as e:
        console.print(f"[red]❌ API health check failed:[/red] {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
