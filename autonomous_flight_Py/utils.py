import sys
import time

from pymavlink import mavutil


def go_to_position(dron, x=0, y=0, z=-15):
    dron.mav.set_position_target_local_ned_send(
        0,
        dron.target_system,
        dron.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111111000,
        x, y, z,
        0, 0, 0,
        0, 0, 0,
        0, 0
    )


def send_velocity(dron, vx=0, vy=0):
    dron.mav.set_position_target_local_ned_send(
        int(time.time() * 1e6) % 4294967295,
        dron.target_system,
        dron.target_component,
        mavutil.mavlink.MAV_FRAME_BODY_NED,
        0b0000111111000111,
        0, 0, 0,
        vx, vy, 0,
        0, 0, 0,
        0, 0
    )


def set_param(dron, name, value):
    dron.mav.param_set_send(
        dron.target_system,
        dron.target_component,
        name.encode('ascii'),
        float(value),
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )


def trigger_relay(index):
    pass


def set_arm(dron):
    dron.mav.command_long_send(
        dron.target_system,
        dron.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,
        0, 0, 0, 0, 0, 0
    )


def set_mode(dron, mode):
    mode_id = dron.mode_mapping()[mode]
    dron.set_mode(mode_id)


def takeoff(dron, alt):
    dron.mav.command_long_send(
        dron.target_system,
        dron.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, alt
    )


def signal_handler(dron, flag, process):
    def handler(signum, frame):
        print(f"Signal({signum}) alindi islemler sonlandiriliyor")
        set_mode(dron, 'RTL')
        flag.value = False
        if process.is_alive():
            process.terminate()
        sys.exit(0)

    return handler
