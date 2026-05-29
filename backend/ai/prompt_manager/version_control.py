"""
Prompt 版本控制系统
支持版本注册、回滚、对比、活跃版本管理
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class PromptVersion:
    """Prompt 版本快照"""
    prompt_id: str
    version: str
    content_hash: str
    system_prompt: str
    user_prompt: str
    variables: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = False
    eval_score: float | None = None
    change_summary: str = ""


@dataclass(frozen=True)
class PromptDiff:
    """Prompt 版本差异"""
    prompt_id: str
    from_version: str
    to_version: str
    system_prompt_changes: dict[str, Any]
    user_prompt_changes: dict[str, Any]
    metadata_changes: dict[str, Any]


class PromptVersionControl:
    """
    Prompt 版本管理器
    - 版本注册与快照
    - 活跃版本管理
    - 版本回滚
    - 版本对比
    """

    def __init__(self) -> None:
        # prompt_id -> list of versions
        self._versions: dict[str, list[PromptVersion]] = {}
        # prompt_id -> active version string
        self._active_versions: dict[str, str] = {}

    def register_version(
        self,
        prompt_id: str,
        version: str,
        system_prompt: str,
        user_prompt: str,
        variables: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        change_summary: str = "",
    ) -> PromptVersion:
        """注册新版本"""
        content = f"{system_prompt}|{user_prompt}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        pv = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            content_hash=content_hash,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            variables=tuple(variables or ()),
            metadata=metadata or {},
            change_summary=change_summary,
        )

        if prompt_id not in self._versions:
            self._versions[prompt_id] = []
        self._versions[prompt_id].append(pv)

        # 如果是第一个版本，自动设为活跃
        if prompt_id not in self._active_versions:
            self._active_versions[prompt_id] = version

        return pv

    def get_active_version(self, prompt_id: str) -> PromptVersion | None:
        """获取当前活跃版本"""
        active_ver = self._active_versions.get(prompt_id)
        if not active_ver:
            return None
        return self.get_version(prompt_id, active_ver)

    def get_version(self, prompt_id: str, version: str) -> PromptVersion | None:
        """获取指定版本"""
        versions = self._versions.get(prompt_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None

    def get_all_versions(self, prompt_id: str) -> list[PromptVersion]:
        """获取所有版本"""
        return list(self._versions.get(prompt_id, []))

    def set_active(self, prompt_id: str, version: str) -> bool:
        """设置活跃版本"""
        versions = self._versions.get(prompt_id, [])
        for v in versions:
            if v.version == version:
                self._active_versions[prompt_id] = version
                return True
        return False

    def rollback(self, prompt_id: str, target_version: str) -> PromptVersion | None:
        """回滚到指定版本"""
        target = self.get_version(prompt_id, target_version)
        if target:
            self._active_versions[prompt_id] = target_version
        return target

    def compare_versions(
        self,
        prompt_id: str,
        version_a: str,
        version_b: str,
    ) -> PromptDiff | None:
        """对比两个版本"""
        va = self.get_version(prompt_id, version_a)
        vb = self.get_version(prompt_id, version_b)

        if not va or not vb:
            return None

        return PromptDiff(
            prompt_id=prompt_id,
            from_version=version_a,
            to_version=version_b,
            system_prompt_changes=self._diff_text(va.system_prompt, vb.system_prompt),
            user_prompt_changes=self._diff_text(va.user_prompt, vb.user_prompt),
            metadata_changes=self._diff_metadata(va.metadata, vb.metadata),
        )

    def update_eval_score(self, prompt_id: str, version: str, score: float) -> bool:
        """更新版本评估分数"""
        versions = self._versions.get(prompt_id, [])
        for i, v in enumerate(versions):
            if v.version == version:
                # 创建新版本（不可变）
                updated = PromptVersion(
                    prompt_id=v.prompt_id,
                    version=v.version,
                    content_hash=v.content_hash,
                    system_prompt=v.system_prompt,
                    user_prompt=v.user_prompt,
                    variables=v.variables,
                    metadata=v.metadata,
                    created_at=v.created_at,
                    is_active=v.is_active,
                    eval_score=score,
                    change_summary=v.change_summary,
                )
                versions[i] = updated
                return True
        return False

    def get_best_version(self, prompt_id: str) -> PromptVersion | None:
        """获取评估分数最高的版本"""
        versions = self._versions.get(prompt_id, [])
        scored = [v for v in versions if v.eval_score is not None]
        if not scored:
            return self.get_active_version(prompt_id)
        return max(scored, key=lambda v: v.eval_score or 0.0)

    def _diff_text(self, text_a: str, text_b: str) -> dict[str, Any]:
        """简单文本差异"""
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()

        added = [l for l in lines_b if l not in lines_a]
        removed = [l for l in lines_a if l not in lines_b]

        return {
            "added": added,
            "removed": removed,
            "changed": len(added) > 0 or len(removed) > 0,
        }

    def _diff_metadata(self, meta_a: dict[str, Any], meta_b: dict[str, Any]) -> dict[str, Any]:
        """元数据差异"""
        all_keys = set(meta_a.keys()) | set(meta_b.keys())
        changes: dict[str, Any] = {}

        for key in all_keys:
            va = meta_a.get(key)
            vb = meta_b.get(key)
            if va != vb:
                changes[key] = {"from": va, "to": vb}

        return changes

    def export_snapshot(self, prompt_id: str) -> dict[str, Any]:
        """导出快照（用于持久化）"""
        versions = self._versions.get(prompt_id, [])
        return {
            "prompt_id": prompt_id,
            "active_version": self._active_versions.get(prompt_id),
            "versions": [
                {
                    "version": v.version,
                    "content_hash": v.content_hash,
                    "system_prompt": v.system_prompt,
                    "user_prompt": v.user_prompt,
                    "variables": list(v.variables),
                    "metadata": v.metadata,
                    "created_at": v.created_at,
                    "eval_score": v.eval_score,
                    "change_summary": v.change_summary,
                }
                for v in versions
            ],
        }

    def import_snapshot(self, snapshot: dict[str, Any]) -> None:
        """导入快照"""
        prompt_id = snapshot["prompt_id"]
        for v_data in snapshot.get("versions", []):
            self.register_version(
                prompt_id=prompt_id,
                version=v_data["version"],
                system_prompt=v_data["system_prompt"],
                user_prompt=v_data["user_prompt"],
                variables=v_data.get("variables"),
                metadata=v_data.get("metadata"),
                change_summary=v_data.get("change_summary", ""),
            )
            if v_data.get("eval_score") is not None:
                self.update_eval_score(prompt_id, v_data["version"], v_data["eval_score"])

        active = snapshot.get("active_version")
        if active:
            self.set_active(prompt_id, active)
