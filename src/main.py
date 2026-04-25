import pygame as pg
from GLWindow import OpenGLWindow

def handle_keydown_event(event, window):
    """
    Handle the keydown event.
    """
    if event.key == pg.K_SPACE:
        window.toggle_animation()
        print(f"Animation running: {window.animation_running}")
    elif event.key == pg.K_0:
        window.target_planet_index = -1
    elif pg.K_1 <= event.key <= pg.K_8:
        window.target_planet_index = event.key - pg.K_1

def handle_mouse_motion(event, window):
    """
    Handle mouse motion for camera rotation.
    If the left mouse button is pressed, rotate the camera.
    """
    if pg.mouse.get_pressed()[0]:  # Left click is held
        dx, dy = event.rel
        window.handle_mouse_movement(dx, dy)

def handle_mouse_wheel(event, window):
    """
    Handle mouse wheel for zooming.
    """
    window.handle_mouse_scroll(event.y)

def main():
    """
    The main function to run the solar system simulation.
    """
    window = OpenGLWindow()
    window.initGL()

    clock = pg.time.Clock()
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                handle_keydown_event(event, window)
            elif event.type == pg.MOUSEMOTION:
                handle_mouse_motion(event, window)
            elif event.type == pg.MOUSEWHEEL:
                handle_mouse_wheel(event, window)

        window.render()
        clock.tick(60)

    window.cleanup()
    pg.quit()

if __name__ == "__main__":
    main()