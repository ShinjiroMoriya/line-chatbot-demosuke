# import requests
import os
from django.conf import settings as st
from PIL import Image
from io import BytesIO


def uploader(event, message_image):
    i = Image.open(BytesIO(message_image))
    filename = event.message.id + '.jpg'
    filename_path = os.path.join(
        st.UPLOADE_DIR, filename)

    if not os.path.exists(st.UPLOADE_DIR):
        os.makedirs(st.UPLOADE_DIR)

    i.save(filename_path)
    # requests.post(
    #     st.URL + '/image',
    #     files={'image': open(filename_path, 'rb')},
    # )
    # if os.path.isfile(st.UPLOADE_DIR + '/' + filename):
    #     os.remove(st.UPLOADE_DIR + '/' + filename)
