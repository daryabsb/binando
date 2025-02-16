import os
import uuid


def upload_image_file_path(instance, filename):
    # Generate file path for new recipe image
    model = instance._meta.model.__name__.lower()
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join(f'uploads/{model}/', filename)


def upload_file_path(instance, filename):
    # Generate file path for new recipe image
    model = instance._meta.model.__name__.lower()
    return os.path.join(f'uploads/files/{model}/', filename)

def upload_barcode_path(instance, filename):
    # Generate file path for new recipe image
    return os.path.join(f'uploads/barcodes/', filename)
