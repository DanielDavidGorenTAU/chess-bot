import json
import os

class LabelingQualityError(Exception):
    pass

class LabelingQualityChecker:
    def __init__(self, allow_orphans: bool = False):
        # We only need to check for orphans now. 
        # Out-of-bounds is no longer an "error" because spatial logic 
        # is actually what determines ownership when no manual relation exists.
        self.allow_orphans = allow_orphans

    def check_file(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)

        total_errors = 0
        report = []

        for task_idx, task in enumerate(tasks):
            task_id = task.get("id", f"Task_{task_idx}")
            image_name = task.get("data", {}).get("image", "Unknown Image")

            for ann_idx, annotation in enumerate(task.get("annotations", [])):
                errors = self._inspect_annotation_logic(annotation, task_id, image_name)
                if errors:
                    total_errors += len(errors)
                    report.extend(errors)

        if total_errors > 0:
            error_msg = f"\nFound {total_errors} labeling logic error(s):\n" + "\n".join(f"- {e}" for e in report)
            raise LabelingQualityError(error_msg)
        
        print("All labeling logic checks passed successfully! No annotation errors found.")

    def _inspect_annotation_logic(self, annotation: dict, task_id, image_name) -> list:
        errors = []
        results = annotation.get("result", [])

        # ---------------------------------------------------------
        # 1. Categorize Annotation Regions
        # ---------------------------------------------------------
        regions_by_id = {}
        relations = []

        for item in results:
            if item.get("type") == "relation":
                relations.append(item)
            elif "id" in item:
                regions_by_id[item["id"]] = item

        # Separate bounding boxes and keypoints for easier iteration
        bboxes = {k: v for k, v in regions_by_id.items() if v.get("type") in ["rectanglelabels", "rectangle"]}
        keypoints = {k: v for k, v in regions_by_id.items() if v.get("type") == "keypointlabels"}

        # ---------------------------------------------------------
        # 2. Map Explicit Manual Relations
        # ---------------------------------------------------------
        explicit_parents = {}
        for rel in relations:
            from_id, to_id = rel.get("from_id"), rel.get("to_id")
            
            # Check if IDs exist
            if from_id not in regions_by_id or to_id not in regions_by_id:
                errors.append(f"[{image_name}] Broken Relation: Points to a missing ID ({from_id} -> {to_id})")
                continue

            # Map the relation: Keypoint -> Bounding Box
            if from_id in keypoints and to_id in bboxes:
                explicit_parents.setdefault(from_id, set()).add(to_id)
            elif to_id in keypoints and from_id in bboxes:
                explicit_parents.setdefault(to_id, set()).add(from_id)

        # ---------------------------------------------------------
        # 3. Determine Final Ownership (The Core Logic)
        # ---------------------------------------------------------
        final_owners = {}          # Maps keypoint_id -> set of bounding_box_ids
        parent_keypoint_labels = {} # Maps bounding_box_id -> list of keypoint labels owned

        for kp_id, kp_region in keypoints.items():
            # RULE 1: Explicit manual relation overrides everything
            if kp_id in explicit_parents and explicit_parents[kp_id]:
                final_owners[kp_id] = explicit_parents[kp_id]
            else:
                # RULE 2: Spatial inclusion (Fallback)
                kp_val = kp_region.get("value", {})
                kp_x, kp_y = kp_val.get("x"), kp_val.get("y")
                
                spatial_parents = set()
                if kp_x is not None and kp_y is not None:
                    # Check every bounding box to see if the point resides inside it
                    for box_id, box_region in bboxes.items():
                        box_val = box_region.get("value", {})
                        bx = box_val.get("x", 0)
                        by = box_val.get("y", 0)
                        bw = box_val.get("width", 0)
                        bh = box_val.get("height", 0)
                        
                        # Point resides in rectangle logic
                        if bx <= kp_x <= (bx + bw) and by <= kp_y <= (by + bh):
                            spatial_parents.add(box_id)
                            
                final_owners[kp_id] = spatial_parents

            # Map the resulting owner(s) to track duplicate labels later
            kp_labels = kp_region.get("value", {}).get("keypointlabels", ["Unknown"])
            for owner_id in final_owners[kp_id]:
                parent_keypoint_labels.setdefault(owner_id, []).extend(kp_labels)

        # ---------------------------------------------------------
        # 4. Run Quality Checks on the Final Ownership Structure
        # ---------------------------------------------------------
        for kp_id, owners in final_owners.items():
            label_str = keypoints[kp_id].get("value", {}).get("keypointlabels", ["Unknown"])[0]

            # MULTI-OWNER ERROR
            # (Happens if a point is manually related to 2 boxes, OR spatially falls inside 2 overlapping boxes)
            if len(owners) > 1:
                errors.append(
                    f"[{image_name}] MULTI-OWNER ERROR: Keypoint '{label_str}' (ID: {kp_id}) "
                    f"is owned by {len(owners)} bounding boxes: {list(owners)}"
                )

            # ORPHAN ERROR
            # (Happens if no manual relation exists AND the point falls outside all bounding boxes)
            elif len(owners) == 0 and not self.allow_orphans:
                errors.append(
                    f"[{image_name}] ORPHAN ERROR: Keypoint '{label_str}' (ID: {kp_id}) "
                    f"has no manual relation and resides outside all bounding boxes."
                )

        # DUPLICATE KEYPOINT ON SAME BOX ERROR
        for parent_id, kp_label_list in parent_keypoint_labels.items():
            seen = set()
            duplicates = set()
            for label in kp_label_list:
                if label in seen:
                    duplicates.add(label)
                seen.add(label)

            if duplicates:
                errors.append(
                    f"[{image_name}] DUPLICATE KEYPOINT: Bounding box '{parent_id}' "
                    f"owns multiple keypoints with the exact same label(s): {list(duplicates)}"
                )

        return errors

if __name__ == "__main__":
    checker = LabelingQualityChecker()

    try:
        checker.check_file("C:/Users/m1478/Downloads/project-9-at-2026-08-08-16-58-656f5227.json")
    except LabelingQualityError as e:
        print(e)