import React from 'react';
import { Divider, List, ListItem, ListItemText, ListItemButton } from "@mui/material";

export function sortByPage(s1, s2, reverse=false) {
    if (s1.source.page < s2.source.page) {
        return reverse ? -1 : 1
    } else if (s1.source.page > s2.source.page) {
        return reverse ? 1 : -1
    }
    return 0
}

export function sortByAlphabet(s1, s2, reverse=false) {
    return s1.name.localeCompare(s2.name) * reverse ? -1 : 1
}

export default function StatblockList( { title, statblocks, onClick, selected, filter, sort }) {

    const index = statblocks ? statblocks.filter(filter ? filter : () => true) : [];
    const sbs = [...index];
    // if(sort) {
    //     sbs.sort(sort)
    // }

    return (
      <List sx={{p:0, m:0}}>
        {title ? <>
        <ListItem key={`sb-item-header-${title}`} sx={{topMargin:"10px", bottomMargin:"10px"}}>
            <ListItemText align="center">
                {title}
            </ListItemText>
        </ListItem>
        <Divider /></> : <></>
        }

        {sbs.map((sb,i) => (<>
            <ListItemButton onClick={() => onClick(i)} selected={selected === i} key={`sb-item-button-${sb.name}-${i}`}>
                <ListItem key={`sb-item-${sb.name}-${i}`}>
                  <ListItemText primary={sb.name} />
                </ListItem>
          </ListItemButton>
          <Divider />
            </>
              ))}
      </List>
    );
  }
  