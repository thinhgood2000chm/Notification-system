# import io
# import os
# import tempfile
#
# import cv2
# from typing import Optional
# from PIL import Image
# from pdf2image import convert_from_path
#
#
# from app.api.v1.setting.event import service_file
# from app.library.constant.file import PREFIX_CONTENT_TYPE_IMAGE, PREFIX_CONTENT_TYPE_VIDEO, CONTENT_TYPE_PDF, \
#     THUMBNAIL_IMAGE_EXTENSION, CONTENT_TYPE_GIF, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT
#
#
# def generate_video_thumbnail_bytes(path_tempfile: str, position: float = 0.5) -> Optional[bytes]:
#     if position < 0 or position >= 1.0:
#         # raise ValueError(f'Position {position} is not between 0.0 and 1.0')
#         return None
#
#     capture = cv2.VideoCapture(path_tempfile)
#
#     total_frame = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
#
#     capture.set(cv2.CAP_PROP_POS_FRAMES, int(total_frame * position))
#
#     _, frame = capture.read()
#     _, buffer = cv2.imencode(f'.{THUMBNAIL_IMAGE_EXTENSION}', frame)
#
#     return generate_image_thumbnail_bytes(io.BytesIO(buffer))
#
#
# def generate_libreoffice_thumbnail_bytes(path_tempfile: str) -> Optional[bytes]:
#     change_to_pdf = f'libreoffice --headless --convert-to pdf {path_tempfile}'
#     os.system(change_to_pdf)
#
#     temp_file_pdf_name = path_tempfile[path_tempfile.rfind('/'):]
#     bytes_str = generate_pdf_thumbnail_bytes(f'.{temp_file_pdf_name}.pdf')
#
#     os.remove(f'.{temp_file_pdf_name}.pdf')
#
#     return bytes_str
#
#
# def generate_pdf_thumbnail_bytes(path_tempfile: str) -> Optional[bytes]:
#     images = convert_from_path(path_tempfile)
#
#     stream_str = io.BytesIO()
#     # số 0 tương ứng với page 0, lần lượt theo sau sẽ là 1 2 3 4
#     images[0].save(stream_str, format=f'{THUMBNAIL_IMAGE_EXTENSION}')
#
#     return generate_image_thumbnail_bytes(stream_str)
#
#
# def generate_image_thumbnail_bytes(input_image_bytesIO: io.BytesIO, content_tye: Optional[str]=None) -> Optional[bytes]: # noqa
#     if content_tye == CONTENT_TYPE_GIF:
#         image = Image.open(input_image_bytesIO).convert('RGB')
#     else:
#         image = Image.open(input_image_bytesIO)
#
#     image.thumbnail(size=(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
#
#     stream_str = io.BytesIO()
#     image.save(stream_str, format=f'{THUMBNAIL_IMAGE_EXTENSION}')
#
#     return stream_str.getvalue()
#
#
# def create_thumbnail_for_file_upload(
#         content_type: str,
#         file: io.BytesIO,
# ) -> None:
#
#     temp_file = tempfile.NamedTemporaryFile()
#     if PREFIX_CONTENT_TYPE_IMAGE in content_type:
#         thumbnail = generate_image_thumbnail_bytes(file, content_type)
#     else:
#         temp_file.write(bytes(file.getbuffer().tobytes()))
#
#         if PREFIX_CONTENT_TYPE_VIDEO in content_type:
#             thumbnail = generate_video_thumbnail_bytes(temp_file.name)
#         elif CONTENT_TYPE_PDF in content_type:
#             thumbnail = generate_pdf_thumbnail_bytes(temp_file.name)
#         else:
#             thumbnail = generate_libreoffice_thumbnail_bytes(temp_file.name)
#
#     temp_file.close()
