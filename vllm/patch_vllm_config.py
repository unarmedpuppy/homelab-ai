"""Build-time patch: add qwen3_5_text to vLLM's config registry.

vLLM maps model_type -> HuggingFace config class in _CONFIG_REGISTRY.
The nightly image has 'qwen3_5' -> Qwen3_5Config (multimodal VL config),
but no entry for 'qwen3_5_text' (text-only model type used by Qwen3.5 text models).

When transformers v5 loads a qwen3_5_text model, the returned config is
Qwen3_5TextConfig. vLLM then fails because it can't find the type in its registry,
and the multimodal Qwen3_5ProcessingInfo.get_hf_config() does a strict isinstance
check against Qwen3_5Config, which Qwen3_5TextConfig fails.

Fix: insert 'qwen3_5_text' -> 'Qwen3_5TextConfig' into _CONFIG_REGISTRY, and
ensure Qwen3_5TextConfig is available in the configs module.
"""
import site
import sys
from pathlib import Path


def find_vllm_config():
    for sp in site.getsitepackages():
        p = Path(sp) / "vllm" / "transformers_utils" / "config.py"
        if p.exists():
            return p
    # Try dist-packages directly
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "transformers_utils" / "config.py"
            if p.exists():
                return p
    raise FileNotFoundError("vllm/transformers_utils/config.py not found")


def find_vllm_configs_init():
    """Find the vllm.transformers_utils.configs package __init__.py"""
    for sp in site.getsitepackages():
        p = Path(sp) / "vllm" / "transformers_utils" / "configs" / "__init__.py"
        if p.exists():
            return p
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "transformers_utils" / "configs" / "__init__.py"
            if p.exists():
                return p
    raise FileNotFoundError("vllm/transformers_utils/configs/__init__.py not found")


def patch_config_registry(config_path: Path):
    src = config_path.read_text()

    # Check if already patched
    if "qwen3_5_text" in src:
        print(f"Already patched (qwen3_5_text already present): {config_path}")
        return

    # Registry uses kwargs syntax: qwen3_5="Qwen3_5Config",
    old = 'qwen3_5="Qwen3_5Config",'
    new = 'qwen3_5="Qwen3_5Config",\n    qwen3_5_text="Qwen3_5TextConfig",'

    if old not in src:
        # Try without trailing comma (last entry)
        old = 'qwen3_5="Qwen3_5Config"'
        if old not in src:
            raise ValueError(
                f"Could not find 'qwen3_5=\"Qwen3_5Config\"' in {config_path}. "
                "vLLM version may have changed. Inspect the file manually."
            )
        new = 'qwen3_5="Qwen3_5Config",\n    qwen3_5_text="Qwen3_5TextConfig"'

    patched = src.replace(old, new, 1)
    config_path.write_text(patched)
    print(f"Patched _CONFIG_REGISTRY: added qwen3_5_text -> Qwen3_5TextConfig in {config_path}")


def patch_configs_init(init_path: Path):
    """Ensure Qwen3_5TextConfig is exported from the configs __init__."""
    src = init_path.read_text()

    if "Qwen3_5TextConfig" in src:
        print(f"Qwen3_5TextConfig already exported in {init_path}")
        return

    # Check if Qwen3_5Config is exported — find and extend that line/block
    if "Qwen3_5Config" not in src:
        print(f"Warning: Qwen3_5Config not found in {init_path} — skipping TextConfig export patch")
        return

    old = "Qwen3_5Config"
    new = "Qwen3_5Config, Qwen3_5TextConfig"

    # Only patch the first occurrence (likely the import or __all__ entry)
    patched = src.replace(old, new, 1)
    init_path.write_text(patched)
    print(f"Patched configs/__init__.py: added Qwen3_5TextConfig export in {init_path}")


def patch_qwen3_5_config_file(config_path: Path):
    """Find the qwen3_5 vLLM config file and ensure Qwen3_5TextConfig is defined/exported."""
    configs_dir = config_path.parent / "configs"
    qwen_config = configs_dir / "qwen3_5.py"

    if not qwen_config.exists():
        print(f"Warning: {qwen_config} not found — skipping qwen3_5 config patch")
        return

    src = qwen_config.read_text()

    if "Qwen3_5TextConfig" in src:
        print(f"Qwen3_5TextConfig already defined in {qwen_config}")
        return

    # Add Qwen3_5TextConfig as an alias at the end of the file
    alias = "\n\n# Text-only config alias for model_type='qwen3_5_text' (transformers v5)\n"
    alias += "try:\n"
    alias += "    from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5TextConfig\n"
    alias += "except ImportError:\n"
    alias += "    # Fallback: alias to Qwen3_5Config if transformers v5 not available\n"
    alias += "    Qwen3_5TextConfig = Qwen3_5Config\n"

    patched = src + alias
    qwen_config.write_text(patched)
    print(f"Patched {qwen_config}: added Qwen3_5TextConfig import/alias")


def find_vllm_models_config():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "model_executor" / "models" / "config.py"
            if p.exists():
                return p
    raise FileNotFoundError("vllm model executor models/config.py not found")


def patch_models_config_map(config_path: Path):
    """Register Qwen3_5ForCausalLM with HybridAttentionMambaModelConfig.

    HybridAttentionMambaModelConfig adjusts the attention block_size so that
    the attention page_size >= mamba state page_size, and pads the mamba page
    size to match. Without this, vLLM's KV cache initialization fails with:
      NotImplementedError: The page size of the layer is not divisible by the
      maximum page size. Cannot unify by adjusting block_size.

    Also sets mamba_ssm_cache_dtype from the model's HF config field.
    HybridAttentionMambaModelConfig is already defined in config.py but not
    registered for Qwen3_5ForCausalLM.
    """
    src = config_path.read_text()

    if "Qwen3_5ForCausalLM_PATCHED" in src:
        print(f"Qwen3_5ForCausalLM already in MODELS_CONFIG_MAP: {config_path}")
        return

    # Inject a combined config class before MODELS_CONFIG_MAP
    new_class = '''
class Qwen3_5ForCausalLMConfig(HybridAttentionMambaModelConfig):
    """Combined config for Qwen3.5 text-only models.
    Applies HybridAttentionMambaModelConfig (block size alignment for
    mamba+attention hybrid KV cache) and sets mamba_ssm_cache_dtype
    from the model's HF config.
    Qwen3_5ForCausalLM_PATCHED
    """
    @classmethod
    def verify_and_update_config(cls, vllm_config: "VllmConfig") -> None:
        # Set mamba_ssm_cache_dtype from HF config BEFORE calling super(),
        # because super() (HybridAttentionMambaModelConfig) uses the dtype to
        # compute mamba page size. Getting it wrong here causes an assertion
        # failure later when the actual layer instantiates with the correct dtype.
        cache_config = vllm_config.cache_config
        hf_text_config = vllm_config.model_config.hf_text_config
        mamba_ssm_dtype = getattr(hf_text_config, "mamba_ssm_dtype", None)
        if cache_config.mamba_ssm_cache_dtype == "auto" and mamba_ssm_dtype is not None:
            cache_config.mamba_ssm_cache_dtype = mamba_ssm_dtype
        super().verify_and_update_config(vllm_config)

'''

    # Add entries to MODELS_CONFIG_MAP
    old = '    "Qwen3_5ForConditionalGeneration": Qwen3_5ForConditionalGenerationConfig,'
    new = (
        '    "Qwen3_5ForCausalLM": Qwen3_5ForCausalLMConfig,\n'
        '    "Qwen3_5MoeForCausalLM": Qwen3_5ForCausalLMConfig,\n'
        '    "Qwen3_5ForConditionalGeneration": Qwen3_5ForConditionalGenerationConfig,'
    )

    if old not in src:
        raise ValueError(
            f"Could not find Qwen3_5ForConditionalGeneration in {config_path}. "
            "vLLM version may have changed."
        )

    # Inject the new class before MODELS_CONFIG_MAP
    map_marker = "MODELS_CONFIG_MAP: dict[str, type[VerifyAndUpdateConfig]] = {"
    if map_marker not in src:
        raise ValueError(f"Could not find MODELS_CONFIG_MAP in {config_path}")

    patched = src.replace(map_marker, new_class + map_marker, 1)
    patched = patched.replace(old, new, 1)
    config_path.write_text(patched)
    print(f"Patched MODELS_CONFIG_MAP: added Qwen3_5ForCausalLM -> HybridAttentionMambaModelConfig in {config_path}")


def patch_qwen3_5_causal_lm_methods():
    """Add get_mamba_state_shape_from_config and related methods to Qwen3_5ForCausalLM.

    HybridAttentionMambaModelConfig.verify_and_update_config calls
    model_cls.get_mamba_state_shape_from_config(vllm_config) to determine the
    mamba state size for page size alignment. This method exists on
    Qwen3_5ForConditionalGeneration but not on Qwen3_5ForCausalLM (which is
    currently just a `pass` subclass of Qwen3_5ForCausalLMBase).
    """
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "model_executor" / "models" / "qwen3_5.py"
            if p.exists():
                _patch_qwen3_5_file(p)
                return
    raise FileNotFoundError("qwen3_5.py not found")


def _patch_qwen3_5_file(path: Path):
    src = path.read_text()

    if "QWEN3_5_CAUSAL_LM_PATCHED" in src:
        print(f"Qwen3_5ForCausalLM already patched: {path}")
        return

    # Replace the `pass` body with the required classmethods
    old = "class Qwen3_5ForCausalLM(Qwen3_5ForCausalLMBase):\n    pass"
    new = (
        "class Qwen3_5ForCausalLM(Qwen3_5ForCausalLMBase):  # QWEN3_5_CAUSAL_LM_PATCHED\n"
        "    # M-RoPE support for text-only Qwen3.5 (uses mrope_section in rope_parameters)\n"
        "    supports_mrope = True  # ClassVar flag for SupportsMRoPE protocol\n"
        "\n"
        "    def get_mrope_input_positions(\n"
        "        self,\n"
        "        input_tokens: list[int],\n"
        "        mm_features: list,\n"
        "    ) -> tuple[torch.Tensor, int]:\n"
        "        # Text-only: sequential positions replicated across all 3 M-RoPE dims\n"
        "        seq_len = len(input_tokens)\n"
        "        positions = torch.arange(seq_len).unsqueeze(0).expand(3, -1).clone()\n"
        "        return positions, 0\n"
        "\n"
        "    @classmethod\n"
        "    def get_mamba_state_shape_from_config(\n"
        "        cls, vllm_config: \"VllmConfig\"\n"
        "    ) -> tuple[tuple[int, int], tuple[int, int]]:\n"
        "        parallel_config = vllm_config.parallel_config\n"
        "        hf_config = vllm_config.model_config.hf_text_config\n"
        "        tp_size = parallel_config.tensor_parallel_size\n"
        "        num_spec = (\n"
        "            vllm_config.speculative_config.num_speculative_tokens\n"
        "            if vllm_config.speculative_config\n"
        "            else 0\n"
        "        )\n"
        "        return MambaStateShapeCalculator.gated_delta_net_state_shape(\n"
        "            tp_size,\n"
        "            hf_config.linear_num_key_heads,\n"
        "            hf_config.linear_num_value_heads,\n"
        "            hf_config.linear_key_head_dim,\n"
        "            hf_config.linear_value_head_dim,\n"
        "            hf_config.linear_conv_kernel_dim,\n"
        "            num_spec,\n"
        "        )\n"
        "\n"
        "    @classmethod\n"
        "    def get_mamba_state_dtype_from_config(\n"
        "        cls,\n"
        "        vllm_config: \"VllmConfig\",\n"
        "    ) -> tuple[torch.dtype, torch.dtype]:\n"
        "        return MambaStateDtypeCalculator.gated_delta_net_state_dtype(\n"
        "            vllm_config.model_config.dtype,\n"
        "            vllm_config.cache_config.mamba_cache_dtype,\n"
        "            vllm_config.cache_config.mamba_ssm_cache_dtype,\n"
        "        )\n"
        "\n"
        "    @classmethod\n"
        "    def get_mamba_state_copy_func(cls) -> tuple:\n"
        "        return MambaStateCopyFuncCalculator.gated_delta_net_state_copy_func()\n"
    )

    if old not in src:
        raise ValueError(
            f"Could not find 'class Qwen3_5ForCausalLM(Qwen3_5ForCausalLMBase):\\n    pass' "
            f"in {path}. File may have changed."
        )

    patched = src.replace(old, new, 1)
    path.write_text(patched)
    print(f"Patched {path}: added get_mamba_state_shape_from_config to Qwen3_5ForCausalLM")


def find_vllm_linear():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "model_executor" / "layers" / "linear.py"
            if p.exists():
                return p
    raise FileNotFoundError("vllm linear.py not found")


def patch_bnb_tp_multiindex(linear_path: Path):
    """Remove the NotImplementedError guard for BNB + TP + multi-index shard IDs.

    vLLM raises NotImplementedError when BitsAndBytes quantization is used with
    tensor parallelism and a tuple shard_id (multi-index, e.g. fused QKV).
    The guard is overly conservative — the logic below it (adjust_bitsandbytes_4bit_shard)
    handles multi-index shards correctly by iterating over each component.
    Removing the guard allows Qwen3.5 (which uses fused QKV with GLA layers) to
    load with BNB quantization across multiple GPUs.
    """
    src = linear_path.read_text()

    if "BNB_TP_MULTIINDEX_PATCHED" in src:
        print(f"BNB TP multi-index already patched: {linear_path}")
        return

    old = (
        "            use_bitsandbytes_4bit = getattr(param, \"use_bitsandbytes_4bit\", False)\n"
        "            if (\n"
        "                use_bitsandbytes_4bit\n"
        "                and isinstance(loaded_shard_id, tuple)\n"
        "                and self.tp_size > 1\n"
        "            ):\n"
        "                raise NotImplementedError(\n"
        "                    \"Shard id with multiple indices is not supported \"\n"
        "                    \"for BNB quantization with TP yet.\"\n"
        "                )\n"
    )

    new = (
        "            use_bitsandbytes_4bit = getattr(param, \"use_bitsandbytes_4bit\", False)\n"
        "            # BNB_TP_MULTIINDEX_PATCHED: removed NotImplementedError guard;\n"
        "            # adjust_bitsandbytes_4bit_shard handles multi-index shards correctly.\n"
    )

    if old not in src:
        raise ValueError(
            f"Could not find BNB+TP guard in {linear_path}. "
            "vLLM version may have changed. Check lines around 'Shard id with multiple indices'."
        )

    patched = src.replace(old, new, 1)
    linear_path.write_text(patched)
    print(f"Patched {linear_path}: removed BNB+TP multi-index NotImplementedError guard")


def find_vllm_bnb_loader():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "model_executor" / "model_loader" / "bitsandbytes_loader.py"
            if p.exists():
                return p
    raise FileNotFoundError("vllm bitsandbytes_loader.py not found")


def patch_bnb_loader_gdn_submodules(bnb_loader_path: Path):
    """Patch BNB loader to correctly TP-shard GDN sub-module weights.

    Problem:
      The BNB loader builds maybe_fused_weights_modules from actual model modules.
      For GDN layers, the fused module is 'in_proj_qkvz' (MergedColumnParallelLinear
      with output_sizes=[key_dim, key_dim, value_dim, value_dim]).
      BUT the checkpoint has SEPARATE weights: 'in_proj_qkv' and 'in_proj_z'.

      The BNB loader checks checkpoint weight names against maybe_fused_weights_modules
      via exact match (weight_name == module_name). 'in_proj_qkv' != 'in_proj_qkvz',
      so it falls to the 'else' (simple row shard) branch. This gives wrong TP splits:
        - TP rank 0 gets ALL of Q + ALL of K + PART of V (rows 0..5119)
        - TP rank 1 gets PART of V (rows 5120..10239)
      instead of the correct per-component split (1024 Q + 1024 K + 3072 V per rank).

      Same issue for 'in_proj_ba' → 'in_proj_b' / 'in_proj_a'.

    Fix:
      After _classify_module_sharding() builds the module table, inject entries
      for the sub-module checkpoint weight names with the correct per-component
      output_sizes derived from the fused module's output_sizes.

      in_proj_qkvz.output_sizes = [key_dim, key_dim, value_dim, value_dim]
        -> in_proj_qkv: output_sizes[0:3] = [key_dim, key_dim, value_dim]
        -> in_proj_z:   output_sizes[3:]  = [value_dim]
      in_proj_ba.output_sizes = [num_v_heads, num_v_heads]
        -> in_proj_b:   output_sizes[0:1] = [num_v_heads]
        -> in_proj_a:   output_sizes[1:]  = [num_v_heads]
    """
    src = bnb_loader_path.read_text()

    if "GDN_SUBMODULE_PATCHED_V2" in src:
        print(f"BNB loader GDN sub-module sharding already patched: {bnb_loader_path}")
        return

    # Find the end of _classify_module_sharding — we need to add code inside
    # the method after the existing loop. The method body ends with:
    # "        elif isinstance(module, FusedMoE) ..."
    # We find the closing of _classify_module_sharding by looking for where
    # the next def starts (or end of class).
    # Simpler: find the specific last elif in the method and append after it.
    old = (
        "            elif isinstance(module, (QKVParallelLinear, MergedColumnParallelLinear)):\n"
        "                self.maybe_fused_weights_modules[name] = module.output_sizes\n"
    )
    new = (
        "            elif isinstance(module, (QKVParallelLinear, MergedColumnParallelLinear)):\n"
        "                self.maybe_fused_weights_modules[name] = module.output_sizes\n"
        "                # GDN_SUBMODULE_PATCHED_V2: also add checkpoint sub-weight entries.\n"
        "                # For in_proj_qkvz, checkpoint has in_proj_qkv (indices 0,1,2)\n"
        "                # and in_proj_z (index 3). Without this, BNB loader uses wrong\n"
        "                # row-sharding for TP, causing NaN in GDN (GatedDeltaNet) layers.\n"
        "                _gdn_sub = {\n"
        "                    'in_proj_qkvz': [\n"
        "                        ('in_proj_qkv', slice(0, 3)),\n"
        "                        ('in_proj_z',   slice(3, None)),\n"
        "                    ],\n"
        "                    'in_proj_ba': [\n"
        "                        ('in_proj_b', slice(0, 1)),\n"
        "                        ('in_proj_a', slice(1, None)),\n"
        "                    ],\n"
        "                }\n"
        "                for _fused, _subs in _gdn_sub.items():\n"
        "                    if name.endswith('.' + _fused) or name == _fused:\n"
        "                        _prefix = name[:-len(_fused)]\n"
        "                        for _sub_name, _sl in _subs:\n"
        "                            _sub_sizes = list(module.output_sizes[_sl])\n"
        "                            if _sub_sizes:\n"
        "                                self.maybe_fused_weights_modules[\n"
        "                                    _prefix + _sub_name\n"
        "                                ] = _sub_sizes\n"
        "                                _dbg = open('/tmp/bnb_gdn_debug.txt', 'a')\n"
        "                                _dbg.write(f'GDN_SUB_ADDED: {_prefix + _sub_name} -> {_sub_sizes}\\n')\n"
        "                                _dbg.close()\n"
    )

    if old not in src:
        raise ValueError(
            f"Could not find QKVParallelLinear/MergedColumnParallelLinear block in "
            f"{bnb_loader_path}. vLLM version may have changed."
        )

    patched = src.replace(old, new, 1)
    bnb_loader_path.write_text(patched)
    print(
        f"Patched {bnb_loader_path}: added GDN sub-module entries to "
        "maybe_fused_weights_modules for correct BNB+TP sharding"
    )


def find_vllm_model_registry():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = pydir / "dist-packages" / "vllm" / "model_executor" / "models" / "registry.py"
            if p.exists():
                return p
    for sp in site.getsitepackages():
        p = Path(sp) / "vllm" / "model_executor" / "models" / "registry.py"
        if p.exists():
            return p
    raise FileNotFoundError("vllm model registry.py not found")


def patch_model_registry(registry_path: Path):
    """Add Qwen3_5ForCausalLM to vLLM's model registry.

    The class exists in qwen3_5.py but is not registered. Without this entry,
    vLLM can't resolve architectures=['Qwen3_5ForCausalLM'] from the model
    config.json and falls back to the multimodal VL model, causing errors.
    """
    src = registry_path.read_text()

    if '"Qwen3_5ForCausalLM"' in src:
        print(f"Qwen3_5ForCausalLM already in model registry: {registry_path}")
        return

    # Find the Qwen3_5ForConditionalGeneration entry and add ForCausalLM before it
    old = '    "Qwen3_5ForConditionalGeneration": ('
    new = (
        '    "Qwen3_5ForCausalLM": ("qwen3_5", "Qwen3_5ForCausalLM"),\n'
        '    "Qwen3_5MoeForCausalLM": ("qwen3_5", "Qwen3_5MoeForCausalLM"),\n'
        '    "Qwen3_5ForConditionalGeneration": ('
    )

    if old not in src:
        raise ValueError(
            f"Could not find Qwen3_5ForConditionalGeneration in {registry_path}. "
            "vLLM version may have changed."
        )

    patched = src.replace(old, new, 1)
    registry_path.write_text(patched)
    print(f"Patched model registry: added Qwen3_5ForCausalLM in {registry_path}")


def patch_bnb_loader_gdn_path_debug(bnb_loader_path: Path):
    """Add file-based debug logging to trace in_proj weight code path at runtime."""
    src = bnb_loader_path.read_text()
    if "GDN_PATH_DEBUG" in src:
        print(f"BNB loader GDN path debug already patched: {bnb_loader_path}")
        return

    # Patch FUSED path to log when in_proj weights hit it
    old_fused = (
        "                elif any(\n"
        "                    check_match(mapped_weight_name, module)\n"
        "                    for module in self.maybe_fused_weights_modules\n"
        "                ):\n"
        "                    # GDN_DEBUG_PATH\n"
        "                    if 'in_proj' in mapped_weight_name:\n"
        "                        matched = [m for m in self.maybe_fused_weights_modules if check_match(mapped_weight_name, m)]\n"
        "                        sizes = self.maybe_fused_weights_modules.get(matched[0], []) if matched else []\n"
        "                        import sys\n"
        "                        print(f'[GDN_DEBUG] FUSED path: {mapped_weight_name} -> sizes={sizes} shape={weight_tensor.shape}', file=sys.stderr, flush=True)\n"
        "                    # special case for fused weights\n"
    )
    # If old debug patch is there, update it; otherwise add fresh
    old_fused_nodebug = (
        "                elif any(\n"
        "                    check_match(mapped_weight_name, module)\n"
        "                    for module in self.maybe_fused_weights_modules\n"
        "                ):\n"
        "                    # special case for fused weights\n"
    )
    new_fused = (
        "                elif any(\n"
        "                    check_match(mapped_weight_name, module)\n"
        "                    for module in self.maybe_fused_weights_modules\n"
        "                ):\n"
        "                    # GDN_PATH_DEBUG\n"
        "                    if 'in_proj' in mapped_weight_name:\n"
        "                        _matched = [m for m in self.maybe_fused_weights_modules if check_match(mapped_weight_name, m)]\n"
        "                        _sizes = self.maybe_fused_weights_modules.get(_matched[0], []) if _matched else []\n"
        "                        with open('/tmp/bnb_gdn_debug.txt', 'a') as _dbg:\n"
        "                            _dbg.write(f'FUSED: {mapped_weight_name} sizes={_sizes} shape={weight_tensor.shape}\\n')\n"
        "                    # special case for fused weights\n"
    )
    # Patch ROW-SHARD path
    old_row = (
        "                # Shard by row\n"
        "                else:\n"
        "                    # GDN_DEBUG_PATH\n"
        "                    if 'in_proj' in mapped_weight_name:\n"
        "                        import sys\n"
        "                        print(f'[GDN_DEBUG] ROW-SHARD path: {mapped_weight_name} shape={weight_tensor.shape}', file=sys.stderr, flush=True)\n"
        "                    total_size = weight_tensor.size(0)\n"
    )
    old_row_nodebug = (
        "                # Shard by row\n"
        "                else:\n"
        "                    total_size = weight_tensor.size(0)\n"
    )
    new_row = (
        "                # Shard by row\n"
        "                else:\n"
        "                    # GDN_PATH_DEBUG\n"
        "                    if 'in_proj' in mapped_weight_name:\n"
        "                        with open('/tmp/bnb_gdn_debug.txt', 'a') as _dbg:\n"
        "                            _dbg.write(f'ROW-SHARD: {mapped_weight_name} shape={weight_tensor.shape}\\n')\n"
        "                    total_size = weight_tensor.size(0)\n"
    )

    patched = src
    for old, new in [(old_fused, new_fused), (old_fused_nodebug, new_fused),
                     (old_row, new_row), (old_row_nodebug, new_row)]:
        if old in patched:
            patched = patched.replace(old, new, 1)
            break

    if patched == src:
        print(f"WARNING: Could not find FUSED or ROW-SHARD target in {bnb_loader_path}")
        return

    # Also patch row shard
    for old, new in [(old_row, new_row), (old_row_nodebug, new_row)]:
        if old in patched:
            patched = patched.replace(old, new, 1)
            break

    bnb_loader_path.write_text(patched)
    print(f"Patched {bnb_loader_path}: added GDN path debug logging")


def find_vllm_bnb_quant():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = (
                pydir
                / "dist-packages"
                / "vllm"
                / "model_executor"
                / "layers"
                / "quantization"
                / "bitsandbytes.py"
            )
            if p.exists():
                return p
    raise FileNotFoundError("vllm quantization/bitsandbytes.py not found")


def patch_bnb_gemm_force(bnb_quant_path: Path):
    """Force GEMM path in BNB matmul_4bit for batch=1 to avoid NaN in GEMV kernel.

    BNB dispatches batch=1 to GEMV, which produces NaN for specific weight rows
    in abliterated Qwen3.5 NF4 weights (z shard at TP=1 and TP=2). The GEMM
    kernel (batch>1) is numerically clean. Fix: pad batch 1->2, run GEMM, slice
    back to batch=1.
    """
    src = bnb_quant_path.read_text()

    if "HAL_GEMM_FORCE" in src:
        print(f"HAL_GEMM_FORCE already patched: {bnb_quant_path}")
        return

    old = (
        "def _apply_bnb_4bit(\n"
        "    x: torch.Tensor,\n"
        "    weight: torch.Tensor,\n"
        "    offsets: torch.Tensor,\n"
        "    out: torch.Tensor,\n"
        ") -> None:\n"
        "    # only load the bitsandbytes module when needed\n"
        "    from bitsandbytes import matmul_4bit\n"
        "\n"
        "    quant_states = weight.bnb_quant_state\n"
        "    current_index = 0\n"
        "    for i in range(len(quant_states)):\n"
        "        output_size = quant_states[i].shape[0]\n"
        "        # It is more efficient to use out kwarg like\n"
        "        # matmul_4bit(..., out = ...).  Infeasible now due to the bug\n"
        "        # https://github.com/TimDettmers/bitsandbytes/issues/1235.\n"
        "        # Need to change  after the bug is fixed.\n"
        "        out[:, current_index : current_index + output_size] = matmul_4bit(\n"
        "            x, weight[offsets[i] : offsets[i + 1]].t(), quant_states[i]\n"
        "        )\n"
        "        current_index += output_size"
    )
    new = (
        "def _apply_bnb_4bit(\n"
        "    x: torch.Tensor,\n"
        "    weight: torch.Tensor,\n"
        "    offsets: torch.Tensor,\n"
        "    out: torch.Tensor,\n"
        ") -> None:\n"
        "    # HAL_GEMM_FORCE: force GEMM path for batch=1 to avoid BNB NF4 GEMV NaN.\n"
        "    # BNB dispatches batch=1 to GEMV which produces NaN for specific weight rows\n"
        "    # in abliterated Qwen3.5 (z shard). GEMM kernel is clean. Pad 1->2, slice back.\n"
        "    from bitsandbytes import matmul_4bit\n"
        "\n"
        "    quant_states = weight.bnb_quant_state\n"
        "    current_index = 0\n"
        "    force_gemm = x.shape[0] == 1\n"
        "    x_compute = torch.cat([x, x], dim=0) if force_gemm else x\n"
        "    for i in range(len(quant_states)):\n"
        "        output_size = quant_states[i].shape[0]\n"
        "        result = matmul_4bit(\n"
        "            x_compute, weight[offsets[i] : offsets[i + 1]].t(), quant_states[i]\n"
        "        )\n"
        "        if force_gemm:\n"
        "            result = result[:1, :]\n"
        "        out[:, current_index : current_index + output_size] = result\n"
        "        current_index += output_size"
    )

    if old not in src:
        raise ValueError(
            f"_apply_bnb_4bit not found in {bnb_quant_path}. vLLM version may have changed."
        )

    patched = src.replace(old, new, 1)
    bnb_quant_path.write_text(patched)
    print(f"Patched {bnb_quant_path}: HAL_GEMM_FORCE applied to _apply_bnb_4bit")


def find_vllm_qwen3_next():
    for base in ["/usr/local/lib", "/usr/lib"]:
        for pydir in sorted(Path(base).glob("python3.*"), reverse=True):
            p = (
                pydir
                / "dist-packages"
                / "vllm"
                / "model_executor"
                / "models"
                / "qwen3_next.py"
            )
            if p.exists():
                return p
    raise FileNotFoundError("vllm model_executor/models/qwen3_next.py not found")


def patch_g_clamp(qwen3_next_path: Path):
    """Clamp g (decay factor) after fused_gdn_gating to prevent -inf→NaN cascade.

    Abliterated Qwen3.5 has A_log > 88 and large 'a' outputs (up to 17152).
    fused_gdn_gating computes g = -exp(A_log) * softplus(a + dt_bias).
    With A_log>88 and large a: g = -inf. In chunk_gated_delta_rule cumsum,
    (-inf) - (-inf) = NaN, poisoning all subsequent token positions.

    Fix: clamp g to -88.0. exp(-88) underflows to 0 in fp32 — functionally
    equivalent to -inf but avoids the NaN in cumsum differences.
    """
    src = qwen3_next_path.read_text()

    if "HAL_G_CLAMP" in src:
        print(f"HAL_G_CLAMP already patched: {qwen3_next_path}")
        return

    # Use surrounding if-block for uniqueness and correct 12-space indentation.
    # The call is inside `if attn_metadata.num_prefills > 0:` (8 spaces),
    # so the gating call itself is at 12 spaces.
    old = (
        "        if attn_metadata.num_prefills > 0:\n"
        "            g, beta = fused_gdn_gating(self.A_log, a, b, self.dt_bias)\n"
    )
    new = (
        "        if attn_metadata.num_prefills > 0:\n"
        "            g, beta = fused_gdn_gating(self.A_log, a, b, self.dt_bias)\n"
        "            g = g.clamp(min=-88.0)  # HAL_G_CLAMP: prevent -inf→NaN in cumsum\n"
    )

    if old not in src:
        raise ValueError(
            f"fused_gdn_gating call (inside if attn_metadata.num_prefills > 0) "
            f"not found in {qwen3_next_path}. vLLM version may have changed."
        )

    patched = src.replace(old, new, 1)
    qwen3_next_path.write_text(patched)
    print(f"Patched {qwen3_next_path}: HAL_G_CLAMP applied after fused_gdn_gating")


if __name__ == "__main__":
    config_path = find_vllm_config()
    print(f"Found vLLM config: {config_path}")

    patch_qwen3_5_config_file(config_path)
    patch_configs_init(find_vllm_configs_init())
    patch_config_registry(config_path)
    patch_model_registry(find_vllm_model_registry())
    patch_bnb_tp_multiindex(find_vllm_linear())
    patch_bnb_loader_gdn_submodules(find_vllm_bnb_loader())
    patch_models_config_map(find_vllm_models_config())
    patch_qwen3_5_causal_lm_methods()
    patch_bnb_gemm_force(find_vllm_bnb_quant())
    patch_g_clamp(find_vllm_qwen3_next())

    print("Done. vLLM config patched for qwen3_5_text + BNB NF4 abliterated model.")
