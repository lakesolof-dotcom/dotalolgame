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
        super().__init__(x, y, radius=14, color="#40b8ff", team="blue", hp=300, speed=3.2, damage=18, attack_range=90, cooldown=20)
        self.mana = 100
        self.max_mana = 100
        self.gold = 0
        self.kills = 0
        self.deaths = 0
        self.respawn_timer = 0

    def cast_q(self, enemies):
        if self.mana < 20:
            return
        self.mana -= 20
        for u in enemies:
            if u.alive and self.dist(u) < 120:
                u.take_damage(40)

    def cast_w(self):
        if self.mana < 25:
            return
        self.mana -= 25
        self.hp = min(self.max_hp, self.hp + 60)


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
        self.enemy_hero = Unit(WIDTH - 130, LANE_Y, 14, "#ffb347", "red", 280, -2.4, 16, 85, 22)
        self.blue_tower = Tower(70, "blue")
        self.red_tower = Tower(WIDTH - 70, "red")

        self.blue_minions = []
        self.red_minions = []
        self.projectiles = []
        self.keys = set()

        self.spawn_timer = 0
        self.enemy_death_handled = False
        self.game_over = False
        self.winner = ""

        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)

    def on_key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "q" and self.hero.alive:
            self.hero.cast_q(self.red_minions + [self.enemy_hero, self.red_tower])
        elif key == "w" and self.hero.alive:
            self.hero.cast_w()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

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

        self.hero.x = min(max(self.hero.x + dx, 20), WIDTH - 20)
        self.hero.y = min(max(self.hero.y + dy, 20), HEIGHT - 20)

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
                break

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
            self.winner = "Синие победили"
        if self.blue_tower.hp <= 0:
            self.game_over = True
            self.winner = "Красные победили"

        if self.hero.alive:
            self.hero.mana = min(self.hero.max_mana, self.hero.mana + 0.08)

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
        self.canvas.create_text(WIDTH / 2, 24, fill="white", text="WASD/стрелки — движение | Q — урон по области | W — лечение")

        for u in [self.blue_tower, self.red_tower, self.hero, self.enemy_hero] + self.blue_minions + self.red_minions:
            self.draw_unit(u)

        self.canvas.create_text(120, 30, fill="#9ed2ff", text=f"HP: {int(self.hero.hp)}  MP: {int(self.hero.mana)}")
        self.canvas.create_text(120, 52, fill="#ffe28f", text=f"Gold: {self.hero.gold}  K/D: {self.hero.kills}/{self.hero.deaths}")

        if self.hero.respawn_timer > 0:
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20, fill="#ffdbdb", font=("Arial", 20, "bold"), text=f"Возрождение через {self.hero.respawn_timer // 60 + 1} сек")

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
        self.render()
        self.root.after(FPS_MS, self.tick)

    def run(self):
        self.spawn_wave()
        self.tick()
        self.root.mainloop()


if __name__ == "__main__":
    Game().run()
