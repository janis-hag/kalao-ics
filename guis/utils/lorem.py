import random

lorem = (
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod '
    'tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim '
    'veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea '
    'commodo consequat. Duis aute irure dolor in reprehenderit in voluptate '
    'velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint '
    'occaecat cupidatat non proident, sunt in culpa qui officia deserunt '
    'mollit anim id est laborum.')

lorem_words = lorem.lower().replace('.', '').replace(',', '').split(' ')


def get_sentence(length):
    message = ' '.join(random.sample(lorem_words, length))
    return message.capitalize() + '.'


def get_paragraph(sentences, length):
    return ' '.join([get_sentence(length) for _ in range(sentences)])


def get_paragraphs(paragraphs, sentences, length):
    return '\n'.join([
        get_paragraph(sentences, length) for _ in range(paragraphs)
    ])
