import os
from PIL import Image, ImageFilter, ImageEnhance, ExifTags
import pillow_heif
import piexif

# Register HEIF plugin
pillow_heif.register_heif_opener()

def correct_orientation(image):
    orientation_key = None
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            orientation_key = orientation
            break
    
    exif = image.getexif()
    if exif is not None and orientation_key in exif:
        orientation = exif[orientation_key]
        if orientation == 3:
            image = image.rotate(180, expand=True)
        elif orientation == 6:
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            image = image.rotate(90, expand=True)
    return image, exif, orientation_key

def add_blurred_borders(image_path, output_path, blur_radius=20):
    # Open the original image
    img = Image.open(image_path).convert("RGB")
    
    # Get the original EXIF data
    exif_dict = piexif.load(img.info['exif']) if 'exif' in img.info else None
    
    # Correct the orientation
    img, exif, orientation_key = correct_orientation(img)
    
    # Calculate the size of the borders to add
    width, height = img.size
    
    if width != height:
        if width > height:
            border_size = (width - height) // 2
            top_border = img.crop((0, 0, width, border_size))
            bottom_border = img.crop((0, height - border_size, width, height))
            
            # Blur the borders
            top_border = top_border.filter(ImageFilter.GaussianBlur(blur_radius))
            bottom_border = bottom_border.filter(ImageFilter.GaussianBlur(blur_radius))
            
            # Create a new image with the borders
            new_height = height + 2 * border_size
            new_img = Image.new("RGB", (width, new_height))
            
            # Paste the original image and the borders into the new image
            new_img.paste(top_border, (0, 0))
            new_img.paste(img, (0, border_size))
            new_img.paste(bottom_border, (0, border_size + height))
        else:
            border_size = (height - width) // 2
            left_border = img.crop((0, 0, border_size, height))
            right_border = img.crop((width - border_size, 0, width, height))
            
            # Blur the borders
            left_border = left_border.filter(ImageFilter.GaussianBlur(blur_radius))
            right_border = right_border.filter(ImageFilter.GaussianBlur(blur_radius))
            
            # Create a new image with the borders
            new_width = width + 2 * border_size
            new_img = Image.new("RGB", (new_width, height))
            
            # Paste the original image and the borders into the new image
            new_img.paste(left_border, (0, 0))
            new_img.paste(img, (border_size, 0))
            new_img.paste(right_border, (border_size + width, 0))
    else:
        # Image is already square
        new_img = img
    
    # Enhance the vibrance of the image
    enhancer = ImageEnhance.Color(new_img)
    new_img = enhancer.enhance(1.1)  # Adjust the factor to improve vibrance

    # Save the result with EXIF data
    if exif_dict:
        if orientation_key:
            exif_dict["0th"][orientation_key] = 1  # Reset orientation to normal
        exif_bytes = piexif.dump(exif_dict)
        new_img.save(output_path, exif=exif_bytes)
    else:
        new_img.save(output_path)

def process_images_in_folder(input_folder, output_folder, blur_radius=20):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic')):
            image_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_blurred_borders' + os.path.splitext(filename)[1])
            add_blurred_borders(image_path, output_path, blur_radius)

# Example usage
input_folder = './Photos à traiter'
output_folder = './Photos traitées'
process_images_in_folder(input_folder, output_folder, blur_radius=80)  # Adjust the blur radius as needed
