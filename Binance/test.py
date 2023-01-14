def test(item):
  item.append(4)
  return item


a = [1, 2, 3]

del a[0]
print(len(a))