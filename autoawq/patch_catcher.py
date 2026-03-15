"""Build-time patch: add __getattr__ to AutoAWQ's Catcher class.

Qwen3.5 uses a hybrid attention architecture where the model forward reads
decoder_layer.layer_type to select the correct attention mask. AutoAWQ wraps
layer 0 in a Catcher module during calibration (init_quant), which intercepts
the first forward pass. Catcher doesn't proxy unknown attributes to self.module,
causing AttributeError: 'Catcher' has no attribute 'layer_type'.

Fix: inject __getattr__ into the Catcher class definition in quantizer.py so
attribute lookups fall through to self.module.
"""
import site
from pathlib import Path

# Find installed quantizer.py
site_packages = site.getsitepackages()[0]
quantizer_path = Path(site_packages) / "awq" / "quantize" / "quantizer.py"
assert quantizer_path.exists(), f"Not found: {quantizer_path}"

src = quantizer_path.read_text()

old = """            def forward(self, *args, **kwargs):
                # assume first input to forward is hidden states
                if len(args) > 0:
                    hidden_states = args[0]
                    del args
                else:
                    first_key = list(kwargs.keys())[0]
                    hidden_states = kwargs.pop(first_key)

                inps.append(hidden_states)
                layer_kwargs.update(kwargs)
                raise ValueError  # early exit to break later inference"""

new = """            def __getattr__(self, name):
                # Proxy unknown attributes to the wrapped module so that
                # model architectures that read layer attributes (e.g.
                # Qwen3.5's layer_type) work during calibration.
                # NOTE: defining __getattr__ on nn.Module overrides PyTorch's
                # own __getattr__ which handles _modules/_parameters/_buffers.
                # We must replicate that logic first, then delegate to self.module.
                try:
                    return super().__getattr__(name)
                except AttributeError:
                    pass
                # Access _modules directly from __dict__ to avoid recursion
                modules = self.__dict__.get("_modules", {})
                if "module" in modules:
                    return getattr(modules["module"], name)
                raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

            def forward(self, *args, **kwargs):
                # assume first input to forward is hidden states
                if len(args) > 0:
                    hidden_states = args[0]
                    del args
                else:
                    first_key = list(kwargs.keys())[0]
                    hidden_states = kwargs.pop(first_key)

                inps.append(hidden_states)
                layer_kwargs.update(kwargs)
                raise ValueError  # early exit to break later inference"""

assert old in src, "Catcher.forward not found — AutoAWQ version may have changed"
patched = src.replace(old, new, 1)
quantizer_path.write_text(patched)
print(f"Patched: {quantizer_path}")
