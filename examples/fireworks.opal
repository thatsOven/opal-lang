package opal: import *;
package random: import randint, uniform;

new <Vector> RESOLUTION = Vector(1280, 720);

new int FIREWORK_SIZE     = 4,
        PARTICLE_SIZE     = 2,
        MIN_PARTICLE_QTY  = 80,
        MAX_PARTICLE_QTY  = 120,
        LIFESPAN_DECREASE = 3,
        ALPHA_CHANGE      = 25,
        ROCKET_FREQ_PERC  = 10;

new float PARTICLE_VELOCITY_MULTIPLIER = 0.98,
          PARTICLE_MAX_INIT_VELOCITY   = 5,
          ROCKET_MAX_INIT_VELOCITY     = 17,
          ROCKET_MIN_INIT_VELOCITY     = 8;

new bool RAINBOW_EXPLOSION = False;

new <Vector> GRAVITY = Vector(0, 0.2);

new <Graphics> graphics = Graphics(RESOLUTION, caption = "Fireworks");

new class Particle {
    new method __init__(pos, color = (255, 255, 255), exploder = False) {
        this.pos          = pos;
        this.acceleration = Vector();

        if exploder {
            this.velocity = Vector(uniform(-1, 1), uniform(-1, 1));
            this.velocity *= uniform(1, PARTICLE_MAX_INIT_VELOCITY);
        } else {
            this.velocity = Vector(0, uniform(-ROCKET_MAX_INIT_VELOCITY, -ROCKET_MIN_INIT_VELOCITY));
        }

        this.color    = color;
        this.lifeSpan = 255;
        this.alive    = True;

        this.exploder = exploder;
    }

    new method applyForce(f) {
        this.acceleration += f;
    }

    new method update() {
        if this.exploder {
            this.velocity *= PARTICLE_VELOCITY_MULTIPLIER;
            this.lifeSpan -= LIFESPAN_DECREASE;
        }

        this.velocity += this.acceleration;
        this.pos      += this.velocity;

        this.acceleration *= 0;

        if this.pos.y >= RESOLUTION.y or this.pos.x < 0 or this.pos.x >= RESOLUTION.x {
            this.alive = False;
        }
    }

    new method isAlive() {
        return this.lifeSpan >= 0 and this.alive;
    }

    new method show() {
        if this.exploder {
            graphics.circle(this.pos, PARTICLE_SIZE, this.color, this.lifeSpan);
        } else {
            graphics.fastCircle(this.pos, FIREWORK_SIZE, this.color);
        }
    }
}

new class Explosion {
    new method __init__(pos, color = None) {
        this.pos = pos;

        if color is None {
            this.color = (randint(0, 255), randint(0, 255), randint(0, 255));
        } else {
            this.color = color;
        }

        this.particles = [];
    }

    new method explode(pos = None) {
        if pos is not None {
            this.pos = pos;
        }

        if RAINBOW_EXPLOSION {
            repeat randint(MIN_PARTICLE_QTY, MAX_PARTICLE_QTY) {
                this.particles.append(Particle(this.pos, (randint(0, 255), randint(0, 255), randint(0, 255)), True));
            }
        } else {
            repeat randint(MIN_PARTICLE_QTY, MAX_PARTICLE_QTY) {
                this.particles.append(Particle(this.pos, this.color, True));
            }
        }
    }

    new method update() {
        for particle in this.particles {
            particle.applyForce(GRAVITY);
            particle.update();
        }

        this.particles = [particle for particle in this.particles if particle.isAlive()];
    }

    new method isAlive() {
        return len(this.particles) > 0;
    }

    new method show() {
        for particle in this.particles {
            particle.show();
        }
    }
}

new class Firework {
    new method __init__(pos = None) {
        this.color = (randint(0, 255), randint(0, 255), randint(0, 255));

        if pos is None {
            this.rocket = Particle(Vector(randint(0, RESOLUTION.x), RESOLUTION.y), this.color);
        } else {
            this.rocket = Particle(pos, this.color);
        }

        this.explosion = Explosion(this.rocket.pos, this.color);

        this.exploded = False;
    }

    new method update() {
        if this.exploded {
            this.explosion.update();
        } else {
            this.rocket.applyForce(GRAVITY);
            this.rocket.update();

            if this.rocket.velocity.y >= 0 {
                this.exploded = True;
                this.explosion.explode(this.rocket.pos);
            }
        }
    }

    new method isAlive() {
        return this.explosion.isAlive() or not this.exploded;
    }

    new method show() {
        if not this.exploded {
            this.rocket.show();
        } else {
            this.explosion.show();
        }
    }
}

new list fireworks  = [],
         explosions = [];

@graphics.event(MOUSEBUTTONDOWN);
new function click(event) {
    global fireworks, explosions;

    match event.button {
        case 1 {
            fireworks.append(Firework(graphics.getMousePos()));
        }
        case 3 {
            explosions.append(Explosion(graphics.getMousePos()));
            explosions[-1].explode();
        }
    }
}

@graphics.update;
new function draw() {
    global fireworks, explosions;

    if randint(0, 100) < ROCKET_FREQ_PERC {
        fireworks.append(Firework());
    }

    graphics.fillAlpha((0, 0, 0), ALPHA_CHANGE);

    for firework in fireworks {
        firework.update();
        firework.show();
    }

    for explosion in explosions {
        explosion.update();
        explosion.show();
    }

    fireworks  = [ firework for  firework in  fireworks if  firework.isAlive()];
    explosions = [explosion for explosion in explosions if explosion.isAlive()];
}

main {
    graphics.run(drawBackground = False);
}
