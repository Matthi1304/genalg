from logging import DEBUG
from panda3d.core import PNMImage


DEBUG = False


class MaskImage():

    def __init__(self, image_path=None, image=None):
        assert image_path is not None or image is not None, "Either image_path or image must be provided"
        if image is not None:
            self.image = image
        else:
            self.image = PNMImage(image_path)
            self.image.setNumChannels(1)
        self.darkness = 1 - self.image.getAverageGray()


    def invert_image(self):
        """
        return a new MaskImage that is the inverted version of this image
        """
        black = PNMImage(self.image.getXSize(), self.image.getYSize(), 1)
        black.fill(0.0)
        white = PNMImage(self.image.getXSize(), self.image.getYSize(), 1)
        white.fill(1.0)
        
        inverted_image = PNMImage()
        inverted_image.copyFrom(self.image)
        # threshold(source: PNMImage, channel: int, threshold: float, lt: PNMImage, ge: PNMImage)
        # For each source pixel (x, y):
        # c = source.get_channel(x, y, channel). 
        # Set this image’s (x, y) to:
        #  if c <  threshold --> take from lt
        #  if c >= threshold --> take from ge
        inverted_image.threshold(self.image, 0, 0.9, white, black)

        return MaskImage(image=inverted_image)
    

    def get_score(self, tmp_image):
        """
        return the level of matching pixels between the mask and the texture 
        (a value between 0 and 1, where 1 is a perfect match)
        """
        tmp_image = self.get_masked_image(tmp_image)
        darkness_after_masking = 1 - tmp_image.getAverageGray()
        score = 1 - (self.darkness - darkness_after_masking) / self.darkness
        return score
    

    def get_masked_image(self, tmp_image):
        # threshold(select_image: PNMImage, channel: int, threshold: float, lt: PNMImage, ge: PNMImage)
        # For each pixel (x, y):
        # s = select_image.get_channel(x, y, channel). Set this image’s (x, y) to:
        # lt.get_xel(x, y) if s < threshold, or
        # ge.get_xel(x, y) if s >= threshold
        # mask_positive.threshold(mask_positive, 0, 0.9, image, mask_positive)
        tmp_image.threshold(self.image, 0, 0.9, tmp_image, self.image)
        return tmp_image


class FitnessFunction():

    def __init__(self, app, mask_image_paths, fitness_function_factor=1.0):
        self.app = app
        self.mask_images = [MaskImage(path) for path in mask_image_paths]
        self.inverted_mask_images = [image.invert_image() for image in self.mask_images]

        self.fitness_function_factor = fitness_function_factor

        self.tmp_image = PNMImage()
        self.tmp_image.copyFrom(self.mask_images[0].image)
        self.tmp_image.setNumChannels(1)

        count = len(self.mask_images)
        self.positions = [(i * (360.0 / count)) for i in range(count)]


    def fitness_function(self, configuration):
        fitness = 0.0
        self.app.set_configuration(configuration)
        for i in range(len(self.mask_images)):
            screenshot = self.app.make_screenshot(self.positions[i])
            screenshot.store(self.tmp_image)
            matchScore = self.mask_images[i].get_score(self.tmp_image)
            if (DEBUG):
                self.tmp_image.write(f"tmp/mask_{i}_match.png")
            screenshot.store(self.tmp_image)
            mismatchScore = self.inverted_mask_images[i].get_score(self.tmp_image)    
            if (DEBUG):
                self.tmp_image.write(f"tmp/mask_{i}_mismatch.png")
            score = matchScore - mismatchScore * self.fitness_function_factor
            fitness += score
        return fitness / len(self.mask_images)
