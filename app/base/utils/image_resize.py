from PIL import Image
import imghdr

SQUARE_FIT_SIZE = 900


def standarize_image_size(image_to_std):
    im = Image.new('RGB', (SQUARE_FIT_SIZE, SQUARE_FIT_SIZE), 'white')
    width, height = image_to_std.size
    diff_width = SQUARE_FIT_SIZE - width
    diff_heigth = SQUARE_FIT_SIZE - height
    width_position = int(diff_width/2.0) if diff_width > 2 else  0
    height_position = int(diff_heigth/2.0) if diff_heigth > 2 else  0

    im.paste(image_to_std, (width_position, height_position))

    return im



def is_valid_image(image_to_validate):
    valid_type_formats = ['png', 'jpg', 'jpeg']
    try:
        #print(f'image to validate: {image_to_validate}')
        im = Image.open(image_to_validate)
        print(f'image format {im.format.lower()}')
        file_type = im.format.lower()
        im.verify()
        im.close()
        if file_type in valid_type_formats:
            return True
        else:
            print(f'{file_type} is not a valid format')
            return False
    except:
        return False


def image_resize(image_to_resize):

    image = Image.open(image_to_resize).convert('RGB')
    width, height = image.size
    #print(f'image size before resizing, width: {width} - height: {height}')

    if width > SQUARE_FIT_SIZE and height > SQUARE_FIT_SIZE:
        # Calculate the new width and height to resize to
        if width > height:
            height = int((SQUARE_FIT_SIZE/width)*height)
            width = SQUARE_FIT_SIZE
        else:
            width = int((SQUARE_FIT_SIZE/height)*width)
            height = SQUARE_FIT_SIZE
        
        image_resized = image.resize((width, height))

        #std_image = standarize_image_size(image_resized)
        return image_resized
    else :
        #new_image = standarize_image_size(image)
        return image

    

