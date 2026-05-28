import seaborn as sns
import matplotlib.pyplot as plt

data = [1, 2, 2.5, 3, 5, 6, 8]
sns.kdeplot(data, fill=True)
plt.show()