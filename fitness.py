from logging import DEBUG
from panda3d.core import PNMImage


class MaskImage():

    def __init__(self, image_path):
        self.image = PNMImage()
        self.image.read(image_path)
        self.image.setNumChannels(1)
        self.darkness = 1 - self.image.getAverageGray()
    

    def get_score(self, texture, tmp_image):
        """
        return the level of matching pixels between the mask and the texture 
        (a value between 0 and 1, where 1 is a perfect match)
        """
        texture.store(tmp_image)
        # threshold(select_image: PNMImage, channel: int, threshold: float, lt: PNMImage, ge: PNMImage)
        # For each pixel (x, y):
        # s = select_image.get_channel(x, y, channel). Set this image’s (x, y) to:
        # lt.get_xel(x, y) if s < threshold, or
        # ge.get_xel(x, y) if s >= threshold"""
        # mask_positive.threshold(mask_positive, 0, 0.9, image, mask_positive)
        tmp_image.threshold(self.image, 0, 0.9, tmp_image, self.image)

        darkness_after_masking = 1 - tmp_image.getAverageGray()
        score = 1 - (self.darkness - darkness_after_masking) / self.darkness
        return score        


BOOST_FACTOR_MATCHING_PIXELS = 1.5


class FitnessFunction():

    def __init__(self, app):
        self.app = app
        self.mask_images = []
        self.inverted_mask_images = []

        for hour in range(12):  
            self.mask_images.append(MaskImage(f"textures/target_{hour}.png"))
            self.inverted_mask_images.append(MaskImage(f"textures/target_{hour}i.png"))

        self.tmp_image = PNMImage()
        self.tmp_image.copyFrom(self.mask_images[0].image)
        self.tmp_image.setNumChannels(1)


    def fitness_function(self, individual):
        fitness = 0.0
        self.app.set_configuration(individual)
        for hour in range(12):
            image = self.app.make_screenshot(hour=hour)
            fitness += self._hour_fitness(image, hour)
        return fitness / 12.0
    

    def _hour_fitness(self, texture_image, hour):
        matchScore = self.mask_images[hour].get_score(texture_image, self.tmp_image)
        mismatchScore = self.inverted_mask_images[hour].get_score(texture_image, self.tmp_image)    
        score = BOOST_FACTOR_MATCHING_PIXELS * matchScore - mismatchScore
        return score