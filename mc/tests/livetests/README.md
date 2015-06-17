## Live tests

Tests that do not mock the core dependencies, including `Docker`.

These are expected to fail on travis, since travis will not provide all of the
required dependencies.

Since real images/containers will be downloaded and built, these tests will take
a non-insignificant amount of time to complete.