import numpy as np

# A physical value carried by a Quantity or passed to ``convert``. Scalars stay
# scalars; arrays are converted elementwise.
Numeric = float | np.ndarray
