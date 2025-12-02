# Kodland Desafio Python Marcus

## Descrição

Este é um jogo roguelike top-down em 2D inspirado em jogos do tipo "survive waves". Você controla um soldado que precisa sobreviver a ondas de zumbis e abater o máximo possível antes de morrer. A dificuldade aumenta conforme você elimina inimigos e passa de nível.

## Como Executar

1. **Tenha Python instalado (versão compatível com Pygame Zero).**
2. **Instale o Pygame Zero:**

   ```bash
   pip install pygame-zero
   ```
3. **Coloque o arquivo do jogo com o nome `main.py` na mesma pasta dos assets.**
4. **Garanta que as pastas/arquivos de assets listados abaixo existam nessa pasta.**
5. **Execute o jogo:**

   ```bash
   pgzrun main.py
   ```



## Controles

### Menu

* **Clique com o mouse** nos botões:

  * **Start** — iniciar nova partida.
  * **Sound: ON/OFF** — alterna música e efeitos.
  * **Exit** — fecha o jogo.

### Durante o Jogo

* **Setas do teclado** ou **W, A, S, D** — mover o personagem (movimento em células com interpolação suave).
* **Segurar o botão esquerdo do mouse** — disparo contínuo em direção ao cursor (o jogo também cria um projétil ao clicar).


## Mecânicas do Jogo

* **HP/Vidas:** O jogador começa com vida limitada (ex.: `player.hp = 5`).
* **Inimigos:** Vários inimigos aparecem periodicamente e se movem dentro de um território; podem perseguir o jogador.
* **Projéteis:** O jogador atira projéteis que danificam inimigos.
* **Animação:** Herói e inimigos possuem animação de sprite para estado parado (idle) e para movimento; inimigos também têm animação de aparição e de morte quando disponível.
* **Dificuldade:** Ao atingir um número de kills, o nível sobe e a taxa de spawn aumenta.
* **Invencibilidade curta:** Ao sofrer dano, o jogador recebe um breve cooldown (`hurt_cooldown`) antes de poder ser atingido de novo.
* **Game Over:** O jogo termina quando a vida do jogador chega a zero.u.

## Assets (necessários)

Coloque os seguintes arquivos/pastas na mesma pasta do `main.py`. Os nomes são importantes — ajuste-os no código se usar nomes diferentes.

## Bibliotecas Utilizadas

* **Pygame Zero (`pgzrun`)** — framework principal (interface `screen`, `images`, `sounds`, `music`, `keyboard`).
* **`math`** — cálculos (distância, normalização).
* **`random`** — posições aleatórias de spawn.
* **`pygame.Rect`** — somente a classe `Rect` importada para desenhar/colisões.

