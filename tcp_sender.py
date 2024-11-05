import cv2
import socket
import struct
import numpy as np
import time
import os

from PIL import ImageGrab

from RadarExtractor import RadarExtractor

use_screen_grab = True

def get_screen():
    screenshot = ImageGrab.grab(all_screens=True)
    screen = np.array(screenshot)
    # frame = screen[2160:, 1927:, ::-1]
    frame = screen[:, :1920, ::-1]
    print(f"[{time.time()}] ATENÇÃO: esse valor deve ser de 1920x1080 -> valor real: ", frame.shape)
    return frame

### Video ###
if not use_screen_grab:
    filename = "C:/Users/Principal/Downloads/TCC_2024_Diego_Vicente-20240731T225921Z-001/TCC_2024_Diego_Vicente/Caso1/radar.mp4"
    video = cv2.VideoCapture(filename)

    fps = video.get(cv2.CAP_PROP_FPS)
    dt = round(1/fps * 1000)

    # comeca a partir do minuto 5 (sem linhas de grade)
    start_frame = fps*5*60
    video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    success, frame = video.read()
else:
    frame = get_screen()
    success = True

# AJUSTAR OS VALORES ABAIXO PARA CENTRALIZAR A VARREDURA NA IMAGEM
radar_radius = 488
radar_center = (806, 539)

radarext = RadarExtractor(radar_radius, radar_center, (frame.shape[0], frame.shape[1]))
obstacles_signature, radar_img = radarext.radar_from_tpn_recording(frame)
###

### Network ###
packet_size = 1024

client_port = 9200
client_ip = "10.1.1.125"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.connect((client_ip, client_port))
file_name = "./tmp_img.jpg"
###

WIDTH = 400

while(True):
    if not use_screen_grab:
        success, frame = video.read()
        video.set(cv2.CAP_PROP_POS_FRAMES, video.get(cv2.CAP_PROP_POS_FRAMES) + fps*1)
    else:
        frame = get_screen()

    if not success:
        print("failed to fetch new frame")
        server_socket.close()
        break

    obstacles_signature, radar_img = radarext.radar_from_tpn_recording(frame)

    cv2.imwrite(file_name, obstacles_signature)

    size = os.stat(file_name).st_size
    server_socket.send(struct.pack('!Q', size))

    bytes_sent = 0
    with open(file_name, 'rb') as img_file:
        data = img_file.read(packet_size if ((size - bytes_sent)//packet_size != 0) else (size - bytes_sent))
        
        while bytes_sent < size:
            bytes_sent += server_socket.send(data)
            data = img_file.read(packet_size if ((size - bytes_sent)//packet_size != 0) else (size - bytes_sent))

        img_file.close()

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):

        if not use_screen_grab: 
            video.release()
        
        server_socket.close()
        break

    time.sleep(1)
