import math
import random
import tkinter as tk

WIDTH, HEIGHT = 1000, 640
FPS_MS = 16
LANE_Y = HEIGHT // 2


class Unit:
    def __init__(self, x, y, radius, color, team, hp, speed, damage, attack_range, cooldown):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.team = team
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.attack_range = attack_range
        self.cooldown = cooldown
        self.cooldown_timer = 0

    def dist(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def can_attack(self, other):
        return self.dist(other) <= self.attack_range

    def take_damage(self, dmg):
        self.hp -= dmg

    @property
    def alive(self):
        return self.hp > 0


class Hero(Unit):
    def __init__(self, x, y):
        super().__init__(x, y, radius=16, color="#4f5a63", team="blue", hp=320, speed=3.2, damage=18, attack_range=90, cooldown=20)
        self.mana = 100
        self.max_mana = 100
        self.gold = 0
        self.kills = 0
        self.deaths = 0
        self.respawn_timer = 0


class Minion(Unit):
    def __init__(self, x, team):
        color = "#8bd46f" if team == "blue" else "#f26a6a"
        speed = 1.1 if team == "blue" else -1.1
        super().__init__(x, LANE_Y + random.randint(-20, 20), radius=8, color=color, team=team, hp=55, speed=speed, damage=8, attack_range=28, cooldown=35)


class Tower(Unit):
    def __init__(self, x, team):
        color = "#4caf50" if team == "blue" else "#f44336"
        super().__init__(x, LANE_Y, radius=22, color=color, team=team, hp=700, speed=0, damage=22, attack_range=180, cooldown=30)


class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python MOBA Prototype (без Ursina)")

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#1d2530", highlightthickness=0)
        self.canvas.pack()

        self.hero = Hero(130, LANE_Y)
        self.enemy_hero = Unit(WIDTH - 130, LANE_Y, 16, "#f1c58b", "red", 300, -2.4, 16, 85, 22)
        self.blue_tower = Tower(70, "blue")
        self.red_tower = Tower(WIDTH - 70, "red")

        self.blue_minions = []
        self.red_minions = []
        self.keys = set()
        self.effects = []

        self.spawn_timer = 0
        self.enemy_death_handled = False
        self.game_over = False
        self.winner = ""

        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)

    def add_effect(self, kind, x, y, ttl, radius=20, color="#ffffff", text=""):
        self.effects.append({"kind": kind, "x": x, "y": y, "ttl": ttl, "max_ttl": ttl, "radius": radius, "color": color, "text": text})

    def on_key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "q" and self.hero.alive:
            self.cast_q()
        elif key == "e" and self.hero.alive:
            self.cast_e_heal()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def cast_q(self):
        if self.hero.mana < 20:
            return
        self.hero.mana -= 20
        self.add_effect("ring", self.hero.x, self.hero.y, ttl=18, radius=120, color="#78d5ff", text="Q")
        for unit in self.red_minions + [self.enemy_hero, self.red_tower]:
            if unit.alive and self.hero.dist(unit) < 120:
                unit.take_damage(40)
                self.add_effect("spark", unit.x, unit.y, ttl=10, radius=14, color="#9be4ff")

    def cast_e_heal(self):
        if self.hero.mana < 25:
            return
        self.hero.mana -= 25
        self.hero.hp = min(self.hero.max_hp, self.hero.hp + 60)
        self.add_effect("pulse", self.hero.x, self.hero.y, ttl=24, radius=28, color="#7dff9a", text="HEAL")

    def spawn_wave(self):
        for i in range(4):
            self.blue_minions.append(Minion(130 - i * 25, "blue"))
            self.red_minions.append(Minion(WIDTH - 130 + i * 25, "red"))

    def move_hero(self):
        if not self.hero.alive:
            return
        dx = dy = 0
        if "a" in self.keys or "left" in self.keys:
            dx -= self.hero.speed
        if "d" in self.keys or "right" in self.keys:
            dx += self.hero.speed
        if "w" in self.keys or "up" in self.keys:
            dy -= self.hero.speed
        if "s" in self.keys or "down" in self.keys:
            dy += self.hero.speed

        prev_x, prev_y = self.hero.x, self.hero.y
        self.hero.x = min(max(self.hero.x + dx, 20), WIDTH - 20)
        self.hero.y = min(max(self.hero.y + dy, 20), HEIGHT - 20)

        if abs(self.hero.x - prev_x) + abs(self.hero.y - prev_y) > 0:
            if random.random() < 0.35:
                self.add_effect("trail", self.hero.x, self.hero.y + self.hero.radius, ttl=10, radius=8, color="#c6d3db")

    def ai_enemy_hero(self):
        if not self.enemy_hero.alive:
            if random.random() < 0.003:
                self.enemy_hero.hp = self.enemy_hero.max_hp
                self.enemy_hero.x = WIDTH - 130
                self.enemy_hero.y = LANE_Y
                self.enemy_death_handled = False
            return

        target_x = WIDTH - 220
        if self.hero.alive and self.enemy_hero.dist(self.hero) < 160:
            target_x = self.hero.x + 90

        if self.enemy_hero.x > target_x:
            self.enemy_hero.x += self.enemy_hero.speed
        elif self.enemy_hero.x < target_x - 20:
            self.enemy_hero.x -= self.enemy_hero.speed

        self.enemy_hero.y += random.uniform(-0.7, 0.7)
        self.enemy_hero.y = min(max(self.enemy_hero.y, 100), HEIGHT - 100)

    def try_attack(self, attacker, possible_targets):
        if not attacker.alive:
            return
        if attacker.cooldown_timer > 0:
            attacker.cooldown_timer -= 1
            return
        for target in possible_targets:
            if target.alive and attacker.can_attack(target):
                target.take_damage(attacker.damage)
                attacker.cooldown_timer = attacker.cooldown
                self.add_effect("hit", target.x, target.y, ttl=9, radius=12, color="#ffd27a")
                break

    def update_effects(self):
        for fx in self.effects:
            fx["ttl"] -= 1
        self.effects = [fx for fx in self.effects if fx["ttl"] > 0]

    def update_units(self):
        for m in self.blue_minions:
            if m.alive:
                m.x += m.speed
        for m in self.red_minions:
            if m.alive:
                m.x += m.speed

        for b in self.blue_minions:
            self.try_attack(b, self.red_minions + [self.enemy_hero, self.red_tower])
        for r in self.red_minions:
            self.try_attack(r, self.blue_minions + [self.hero, self.blue_tower])

        self.try_attack(self.hero, self.red_minions + [self.enemy_hero, self.red_tower])
        self.try_attack(self.enemy_hero, self.blue_minions + [self.hero, self.blue_tower])
        self.try_attack(self.blue_tower, self.red_minions + [self.enemy_hero])
        self.try_attack(self.red_tower, self.blue_minions + [self.hero])

        self.blue_minions = [m for m in self.blue_minions if m.alive and -40 < m.x < WIDTH + 40]
        self.red_minions = [m for m in self.red_minions if m.alive and -40 < m.x < WIDTH + 40]

        if self.hero.hp <= 0 and self.hero.respawn_timer == 0:
            self.hero.deaths += 1
            self.hero.respawn_timer = 240

        if self.hero.respawn_timer > 0:
            self.hero.respawn_timer -= 1
            if self.hero.respawn_timer == 0:
                self.hero.hp = self.hero.max_hp
                self.hero.mana = self.hero.max_mana
                self.hero.x, self.hero.y = 130, LANE_Y

        if self.enemy_hero.hp <= 0:
            self.enemy_hero.hp = 0

        if self.enemy_hero.hp <= 0 and not self.enemy_death_handled:
            self.hero.kills += 1
            self.hero.gold += 120
            self.enemy_death_handled = True

        if self.red_tower.hp <= 0:
            self.game_over = True
            self.winner = "Яспер победил"
        if self.blue_tower.hp <= 0:
            self.game_over = True
            self.winner = "Хитрый кот победил"

        if self.hero.alive:
            self.hero.mana = min(self.hero.max_mana, self.hero.mana + 0.08)

    def draw_effects(self):
        for fx in self.effects:
            progress = fx["ttl"] / fx["max_ttl"]
            radius = fx["radius"] * (1.4 - progress)
            x, y = fx["x"], fx["y"]
            if fx["kind"] in {"ring", "pulse"}:
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=fx["color"], width=2)
            elif fx["kind"] == "trail":
                self.canvas.create_oval(x - radius / 2, y - radius / 2, x + radius / 2, y + radius / 2, fill=fx["color"], outline="")
            else:
                self.canvas.create_oval(x - radius / 1.8, y - radius / 1.8, x + radius / 1.8, y + radius / 1.8, fill=fx["color"], outline="")

            if fx["text"]:
                self.canvas.create_text(x, y - radius - 12, fill=fx["color"], text=fx["text"], font=("Arial", 10, "bold"))

    def draw_cat_hero(self, unit, name, team):
        if not unit.alive:
            return

        body = "#3c3a3f" if team == "blue" else "#f0c494"
        ear = "#2b2a2d" if team == "blue" else "#dfa56b"
        eye = "#d6d06b" if team == "blue" else "#8b4a2e"

        # ears
        self.canvas.create_polygon(unit.x - 11, unit.y - 6, unit.x - 2, unit.y - 23, unit.x + 2, unit.y - 4, fill=ear, outline="")
        self.canvas.create_polygon(unit.x + 11, unit.y - 6, unit.x + 2, unit.y - 23, unit.x - 2, unit.y - 4, fill=ear, outline="")
        # head
        self.canvas.create_oval(unit.x - unit.radius, unit.y - unit.radius, unit.x + unit.radius, unit.y + unit.radius, fill=body, outline="")
        # eyes
        self.canvas.create_oval(unit.x - 9, unit.y - 3, unit.x - 2, unit.y + 1, fill=eye, outline="")
        self.canvas.create_oval(unit.x + 2, unit.y - 3, unit.x + 9, unit.y + 1, fill=eye, outline="")
        # nose and mouth
        self.canvas.create_oval(unit.x - 2, unit.y + 2, unit.x + 2, unit.y + 6, fill="#1f1f1f", outline="")
        self.canvas.create_line(unit.x, unit.y + 6, unit.x - 4, unit.y + 10, fill="#1f1f1f", width=2)
        self.canvas.create_line(unit.x, unit.y + 6, unit.x + 4, unit.y + 10, fill="#1f1f1f", width=2)

        if team == "blue":
            # scarf to resemble Jasper meme
            self.canvas.create_arc(unit.x - 12, unit.y + 6, unit.x + 12, unit.y + 20, start=0, extent=180, style=tk.CHORD, fill="#6a3d2c", outline="")

        hp_w = 40
        ratio = max(0, unit.hp / unit.max_hp)
        self.canvas.create_rectangle(unit.x - hp_w / 2, unit.y - unit.radius - 12, unit.x + hp_w / 2, unit.y - unit.radius - 8, fill="#2f2f2f", outline="")
        self.canvas.create_rectangle(unit.x - hp_w / 2, unit.y - unit.radius - 12, unit.x - hp_w / 2 + hp_w * ratio, unit.y - unit.radius - 8, fill="#61ff77", outline="")
        self.canvas.create_text(unit.x, unit.y + unit.radius + 10, text=name, fill="#ffffff", font=("Arial", 8, "bold"))

    def draw_unit(self, u):
        if not u.alive:
            return
        self.canvas.create_oval(u.x - u.radius, u.y - u.radius, u.x + u.radius, u.y + u.radius, fill=u.color, outline="")
        hp_w = 36
        ratio = max(0, u.hp / u.max_hp)
        self.canvas.create_rectangle(u.x - hp_w / 2, u.y - u.radius - 12, u.x + hp_w / 2, u.y - u.radius - 8, fill="#2f2f2f", outline="")
        self.canvas.create_rectangle(u.x - hp_w / 2, u.y - u.radius - 12, u.x - hp_w / 2 + hp_w * ratio, u.y - u.radius - 8, fill="#61ff77", outline="")

    def render(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, LANE_Y - 60, WIDTH, LANE_Y + 60, fill="#33495e", outline="")
        self.canvas.create_text(
            WIDTH / 2,
            24,
            fill="white",
            text="WASD/стрелки — движение | Q — круговой удар | E — лечение (исправлено: не на W)",
        )

        self.draw_unit(self.blue_tower)
        self.draw_unit(self.red_tower)
        for u in self.blue_minions + self.red_minions:
            self.draw_unit(u)

        self.draw_cat_hero(self.hero, "Яспер", "blue")
        self.draw_cat_hero(self.enemy_hero, "Хитрый кот", "red")
        self.draw_effects()

        self.canvas.create_text(130, 30, fill="#9ed2ff", text=f"HP: {int(self.hero.hp)}  MP: {int(self.hero.mana)}")
        self.canvas.create_text(130, 52, fill="#ffe28f", text=f"Gold: {self.hero.gold}  K/D: {self.hero.kills}/{self.hero.deaths}")

        if self.hero.respawn_timer > 0:
            self.canvas.create_text(
                WIDTH / 2,
                HEIGHT / 2 - 20,
                fill="#ffdbdb",
                font=("Arial", 20, "bold"),
                text=f"Возрождение через {self.hero.respawn_timer // 60 + 1} сек",
            )

        if self.game_over:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="")
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2, fill="white", font=("Arial", 34, "bold"), text=self.winner)

    def tick(self):
        if not self.game_over:
            self.spawn_timer += 1
            if self.spawn_timer >= 300:
                self.spawn_wave()
                self.spawn_timer = 0
            self.move_hero()
            self.ai_enemy_hero()
            self.update_units()
            self.update_effects()
        self.render()
        self.root.after(FPS_MS, self.tick)

    def run(self):
        self.spawn_wave()
        self.tick()
        self.root.mainloop()


if __name__ == "__main__":
    Game().run()
