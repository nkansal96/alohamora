exports.asyncWait = time =>
  new Promise(resolve => setTimeout(resolve, time));

exports.arrayMin = arr => {
  let minElem = arr[0];
  for (const el of arr) {
    minElem = Math.min(minElem, el);
  }
  return minElem;
};

exports.arraySum = arr =>
  arr.reduce((acc, v) => acc + v, 0);
