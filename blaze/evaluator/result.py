import itertools

class Result():
  def __init__(self, **res):
    self.speed_index = res.get('speedIndex', 0)

  def __repr__(self):
    return 'Result<{}>'.format(' '.join(itertools.starmap('{}={}'.format, vars(self).items())))
