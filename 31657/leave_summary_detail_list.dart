getTotal(summary) {
  var noofday, broughtforward, taken, total, remain, entitled;
  if (summary['noofdays'] == "") {
    noofday = 0.0;
  } else {
    noofday = double.parse(summary['noofdays']);
  }
  if (summary['broughtforward'] == "") {
    broughtforward = 0.0;
  } else {
    broughtforward = double.parse(summary['broughtforward']);
  }
  if (summary['taken'] == "") {
    taken = 0.0;
  } else {
    taken = double.parse(summary['taken']);
  }
  if (summary['opening'].toString() == "") {
    total = noofday + broughtforward;
  } else {
    var opening = double.parse(summary['opening']);
    total = broughtforward + opening;
  }
  entitled = total - taken;
  var _total = showDecimal(total);
  var _taken = showDecimal(taken);
  var _entitled = showDecimal(entitled);

  return _entitled + " / " + _total;
}
