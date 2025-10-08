from influencer_assistant.training.dataset import build_training_dataset


def test_dataset_examples_have_inputs_and_targets():
    examples = build_training_dataset()
    assert examples, "training dataset should not be empty"
    for example in examples:
        # Check input fields
        assert example.profile_context
        assert example.request
        # Check output fields (structured idea format)
        assert example.idea1_title
        assert example.idea1_summary
        assert example.idea1_pillar
        assert example.idea2_title
        assert example.idea2_summary
        assert example.idea2_pillar
        assert example.idea3_title
        assert example.idea3_summary
        assert example.idea3_pillar
