import random
import sys

def random_word_between_1_20_chars():
    """Funkcja oparta o klasyczne prawdopodobieństwo generuje 'słowa' złożone z krótkich ciągów liter mających
    symulować sylaby. Długość sylab nie jest dokładnie ograniczona, ale
    długości sylab większe niż preferred_max_syll_len będą występowały bardzo rzadko i nie będą dużo wyższe."""
    word = ''
    length = random.randrange(1, 20, 1)#random.randrange(start, stop[, step]) https://docs.python.org/3/library/random
    consonants = "bcdfghjklmnpqrstvwxyzćłńśźż"
    vowels = "aeiouąęó"
    probabilistic_tuple_for_char_choice = lambda x: tuple([1,0] + [0 for i in range(x-2)])\
    [0:random.randrange(2,x + 1 if (x>1) else 3,1)]#Creates a tuple such as (1,0,0). More zeros (x) - longer syllables.
    preferred_max_syll_len = 5

    word = word.join(random.choice((consonants, vowels)\
    [random.choice(probabilistic_tuple_for_char_choice(preferred_max_syll_len))]) for i in range(length))
    return word