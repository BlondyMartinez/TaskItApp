import React, { useContext, useEffect, useState } from "react";
import { Context } from "../../store/appContext";
import AppliedToTask from "./applied_to_task_card.jsx";

const AppliedToTaskList = () => {
    const { store } = useContext(Context);
    const [tasks, setTasks] = useState([]);

    useEffect(() => {
        if (store.user.role === "task_seeker" || store.user.role === "both") {
            const controller = new AbortController(); 
            const signal = controller.signal; 

            loadInfo(signal); 

            return () => {
                controller.abort(); 
            };
        }
    }, [store.user.role]);

    useEffect(() => {
        const controller = new AbortController(); 
        const signal = controller.signal; 

        loadInfo(signal); 

        return () => {
            controller.abort();
        };
    }, [store.notifications]);

    const loadInfo = () => {
        fetch(process.env.BACKEND_URL + `/api/users/${store.user.id}/applications`)
        .then(response => response.json())
        .then(data => setTasks(data))
        .catch(error => console.error(error));
    }
    

    return (
        <div className="container-fluid px-5 bg-light">
            <h3>Applications</h3>
            <div className="row">
                { tasks.length == 0 
                    ? <div>You haven't applied to tasks yet.</div>
                    : tasks.slice().reverse().map((task) => {
                        return (
                            <React.Fragment key={task.id + "att"}>
                                <AppliedToTask taskInfo={task}></AppliedToTask>
                            </React.Fragment>
                        );
                    })
                }
            </div>
        </div>
    );
}

export default AppliedToTaskList;