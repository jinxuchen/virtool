import { UPDATE_SETTINGS } from "../../../app/actionTypes";
import { SampleRights, mapStateToProps, mapDispatchToProps } from "../SampleRights";

describe("<SampleRights />", () => {
    let props;

    beforeEach(() => {
        props = {
            sampleGroup: "force_choice",
            group: "rw",
            all: "rw",
            onChangeSampleGroup: jest.fn(),
            onChangeRights: jest.fn()
        };
    });

    it("should render", () => {
        const wrapper = shallow(<SampleRights {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("should call props.onChangeSampleGroup() when input changes", () => {
        const wrapper = shallow(<SampleRights {...props} />);
        const e = {
            target: {
                value: "users_primary_group"
            }
        };
        wrapper
            .find("InputError")
            .at(0)
            .simulate("change", e);
        expect(props.onChangeSampleGroup).toHaveBeenCalledWith("users_primary_group");
    });

    it.each(["group", "all"])("should call props.onChangeRights() when %p input changes", scope => {
        const wrapper = shallow(<SampleRights {...props} />);
        const e = {
            target: {
                value: "r"
            }
        };
        wrapper
            .find("InputError")
            .at(scope === "group" ? 1 : 2)
            .simulate("change", e);
        expect(props.onChangeRights).toHaveBeenCalledWith(scope, "r");
    });
});

describe("mapStateToProps", () => {
    let state;
    let expected;

    beforeEach(() => {
        state = {
            settings: {
                data: {
                    sample_group: "force_choice",
                    sample_group_read: false,
                    sample_group_write: false,
                    sample_all_read: false,
                    sample_all_write: false
                }
            }
        };
        expected = { group: "", all: "", sampleGroup: "force_choice" };
    });

    it.each([
        ["group", true, true, "rw"],
        ["group", true, false, "r"],
        ["group", false, true, "w"],
        ["group", false, false, ""],
        ["all", true, true, "rw"],
        ["all", true, false, "r"],
        ["all", false, true, "w"],
        ["all", false, false, ""]
    ])("should return props when %p rw rights are (%p, %p)", (scope, read, write, result) => {
        state.settings.data[`sample_${scope}_read`] = read;
        state.settings.data[`sample_${scope}_write`] = write;
        expect(mapStateToProps(state)).toEqual({
            ...expected,
            [scope]: result
        });
    });

    it.each();
});

describe("mapDispatchToProps()", () => {
    let dispatch;
    let props;

    beforeEach(() => {
        dispatch = jest.fn();
        props = mapDispatchToProps(dispatch);
    });

    it("should return onChangeSampleGroup in props", () => {
        props.onChangeSampleGroup("force_choice");
        expect(dispatch).toHaveBeenCalledWith({
            type: UPDATE_SETTINGS.REQUESTED,
            update: { sample_group: "force_choice" }
        });
    });

    it.each([
        ["group", "rw", true, true],
        ["group", "r", true, false],
        ["group", "w", false, true],
        ["group", "", false, false],
        ["all", "rw", true, true],
        ["all", "r", true, false],
        ["all", "w", false, true],
        ["all", "", false, false]
    ])("should return onChangeRights in props that works when %s right string is %p", (scope, str, read, write) => {
        props.onChangeRights(scope, str);
        expect(dispatch).toHaveBeenCalledWith({
            type: UPDATE_SETTINGS.REQUESTED,
            update: {
                [`sample_${scope}_read`]: read,
                [`sample_${scope}_write`]: write
            }
        });
    });
});
