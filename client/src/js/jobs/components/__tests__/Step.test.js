jest.mock("../../utils");

import { getStepDescription } from "../../utils";
import JobStep, { JobStepDescription, JobStepIcon } from "../Step";

describe("<JobStepDescription />", () => {
    let props;

    getStepDescription.mockImplementation((stage, state, task) => ({
        title: "Foo",
        description: "Bar"
    }));

    beforeEach(() => {
        props = {
            stage: "bowtie_build",
            state: "running",
            task: "create_subtraction"
        };
    });

    it("renders and calls getStepDescription", () => {
        const wrapper = shallow(<JobStepDescription {...props} />);
        const { stage, state, task } = props;
        expect(getStepDescription).toHaveBeenCalledWith(stage, state, task);
        expect(wrapper).toMatchSnapshot();
    });
});

describe("<JobStepIcon />", () => {
    let props;

    beforeEach(() => {
        props = {
            complete: false,
            state: "running"
        };
    });

    it("renders correct icon when step complete", () => {
        props.complete = true;
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("renders correct icon when state complete", () => {
        props.state = "complete";
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("renders correct icon when state running", () => {
        props.state = "running";
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("renders correct icon when state cancelled", () => {
        props.state = "cancelled";
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("renders correct icon when state error", () => {
        props.state = "error";
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });

    it("renders correct icon when state waiting", () => {
        props.state = "waiting";
        const wrapper = shallow(<JobStepIcon {...props} />);
        expect(wrapper).toMatchSnapshot();
    });
});

describe;
